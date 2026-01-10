import os
import asyncio
import logging
import json
from pathlib import Path
from fastmcp import FastMCP
from .valve import valve
from .vault import manager
from .dashboard import dashboard
from .cache import cache

# 1. Configuration and Logging Setup
CONFIG_DIR = Path.home() / ".gemini" / "antigravity"
LOG_FILE = CONFIG_DIR / "mcpv_debug.log"
ROOT_PATH_FILE = CONFIG_DIR / "root_path.txt"

# Ensure config directory exists (before logger is available)
try: 
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except OSError as e: 
    print(f"[mcpv] Warning: Could not create config dir: {e}", file=__import__('sys').stderr)

# Now configure logging (after directory exists)
logging.basicConfig(filename=str(LOG_FILE), level=logging.DEBUG, force=True, encoding="utf-8")
logger = logging.getLogger("mcpv-router")

# Set current working directory from saved root path
if ROOT_PATH_FILE.exists():
    try:
        os.chdir(Path(ROOT_PATH_FILE.read_text(encoding="utf-8").strip()).resolve())
    except (OSError, ValueError) as e: 
        logger.warning(f"Could not change to root path: {e}")
ROOT_DIR = Path.cwd().resolve()

mcp = FastMCP("mcpv")

# === 🌟 [Core 1] Global Tool Registry (Map) ===
# Structure: { "tool_name": { "server": "server_name", "desc": "description...", "args": "arg1, arg2" } }
TOOL_REGISTRY = {}

async def _build_registry():
    """Scans all upstream servers and builds a tool registry map."""
    global TOOL_REGISTRY
    from .vault import BACKUP_FILE
    
    if not BACKUP_FILE.exists(): return
    
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    active_servers = [k for k, v in config.get("mcpServers", {}).items() if not v.get("disabled")]
    
    # Parallel connection attempts
    tasks = [manager.get_session(name) for name in active_servers]
    sessions = await asyncio.gather(*tasks, return_exceptions=True)
    
    new_registry = {}
    
    for name, session in zip(active_servers, sessions):
        if not session or isinstance(session, Exception): continue
        try:
            # Get tool list with timeout
            tools = await asyncio.wait_for(session.list_tools(), timeout=3.0)
            for t in tools.tools:
                # Prevent tool name conflicts: if already exists, register as 'server_toolname'
                key = t.name
                if key in new_registry:
                    key = f"{name}_{t.name}"  # Add prefix on collision
                
                args = list(t.inputSchema.get("properties", {}).keys())
                new_registry[key] = {
                    "server": name,
                    "real_name": t.name,  # Actual name to call
                    "desc": t.description[:100] if t.description else "No description",
                    "args": ", ".join(args)
                }
        except asyncio.TimeoutError:
            logger.warning(f"Timeout listing tools from server '{name}'")
        except Exception as e:
            logger.warning(f"Error getting tools from '{name}': {e}")
            
    TOOL_REGISTRY = new_registry
    logger.info(f"🗺️ Tool Registry Built: {len(TOOL_REGISTRY)} tools found.")

# === 🌟 [Core 2] Smart Context Injection ===
@mcp.tool()
async def get_initial_context(force: bool = False) -> str:
    """
    [System Start] Initializes the session.
    Returns a 'Tool Manual' so you know what tools are available.
    Does NOT return full code context to save tokens (use 'read_file' if needed).
    """
    # 1. Valve check (rate limiting)
    allowed, msg = valve.check(force)
    if not allowed: return msg
    
    # 2. Build registry (wake up servers)
    await _build_registry()
    
    if not TOOL_REGISTRY:
        return "⚠️ No tools found in connected MCP servers."

    # 3. Generate tool manual
    manual = [
        "=== 🎮 MCPV SMART CONSOLE ===",
        "You have access to the following tools. DO NOT use 'use_upstream_tool'.",
        "JUST use 'run_tool(name=...)' directly.\n",
        "--- Available Tools ---"
    ]
    
    # Format tool list nicely
    for tool_name, info in TOOL_REGISTRY.items():
        manual.append(f"🔹 {tool_name}")
        manual.append(f"   └─ Args: {info['args']}")
        manual.append(f"   └─ Desc: {info['desc']}")
    
    manual.append("\n=== [Instruction] ===")
    manual.append("To execute any tool above, use:")
    manual.append("run_tool(tool_name='TOOL_NAME', args={...})")
    manual.append("Example: run_tool(tool_name='query-docs', args={'query': 'nextjs'})")
    
    return "\n".join(manual)

# === 🌟 [Core 3] Unified Execution Tool (Flattened Execution) ===
# === 🌟 [Upgrade] Smart Execution Tool (with Auto-Correction + Caching) ===
@mcp.tool()
async def run_tool(tool_name: str, args: dict = {}, bypass_cache: bool = False) -> str:
    """
    Executes ANY tool from the available list.
    Smart Router: Automatically finds the correct server for the tool.
    Results are cached to reduce redundant calls (unless bypass_cache=True).
    """
    # 1. Load registry (build if empty)
    if not TOOL_REGISTRY:
        await _build_registry()
        
    # 2. Exact match (Happy Path)
    info = TOOL_REGISTRY.get(tool_name)
    
    # 3. [NEW] On match failure: Agent mistake correction logic
    if not info:
        # A. Did agent confuse server name with tool name? (e.g., context-7 -> context7)
        # Extract server list from tool registry
        known_servers = set(t['server'] for t in TOOL_REGISTRY.values())
        
        # Normalize input and server names (remove special chars, lowercase) for comparison
        normalized_input = tool_name.replace("-", "").replace("_", "").lower()
        
        target_server = None
        for sv in known_servers:
            if normalized_input == sv.replace("-", "").replace("_", "").lower():
                target_server = sv
                break
        
        if target_server:
            # Find actual tools belonging to this server and suggest them
            server_tools = [
                f"'{name}' (Args: {i['args']})" 
                for name, i in TOOL_REGISTRY.items() 
                if i['server'] == target_server
            ]
            return (
                f"🛑 Error: '{tool_name}' appears to be a SERVER name (or typo), not a TOOL name.\n"
                f"The server '{target_server}' has the following tools:\n"
                f"{chr(10).join(['- ' + t for t in server_tools])}\n\n"
                f"👉 Please retry 'run_tool' with one of the tool names above."
            )

        # B. Simple typo in tool name? (similarity search)
        candidates = [k for k in TOOL_REGISTRY.keys() if tool_name in k or k in tool_name]
        if candidates:
            return f"❌ Tool '{tool_name}' not found. Did you mean one of these?\n- " + "\n- ".join(candidates)
            
        return f"❌ Tool '{tool_name}' not found in Registry. Please call 'get_initial_context' to see the full menu."

    # 4. Check cache (unless bypassed)
    cache_key = cache.generate_key(tool_name, args)
    if not bypass_cache:
        cached_entry = cache.get(cache_key)
        if cached_entry:
            dashboard.log_tool_call(tool_name, info['server'], 0, success=True)
            return f"[📦 Cached - {cached_entry.hit_count} hits]\n{cached_entry.result}"

    # 5. Execute tool with timing
    server_name = info['server']
    real_tool_name = info['real_name']
    start_time = asyncio.get_event_loop().time()
    
    try:
        session = await manager.get_session(server_name)
        if not session:
            dashboard.log_tool_call(tool_name, server_name, 0, success=False)
            return f"❌ Failed to connect to server '{server_name}'."

        result = await session.call_tool(real_tool_name, args)
        
        # Calculate latency
        latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        dashboard.log_tool_call(tool_name, server_name, latency_ms, success=True)
        
        output = []
        if hasattr(result, 'content'):
            for c in result.content:
                if c.type == "text": output.append(c.text)
                else: output.append(f"[{c.type} content]")
        
        final_res = "\n".join(output) if output else "✅ Executed (No output)"
        
        # 6. Cache the result
        cache.set(cache_key, final_res, tool_name=tool_name)
        
        return final_res
        
    except Exception as e:
        logger.error(f"Tool execution error: {tool_name} -> {e}")
        return f"❌ Execution Error ({server_name} -> {tool_name}): {e}"

# Configurable file size limit
MAX_FILE_SIZE_MB = float(os.environ.get("MCPV_MAX_FILE_SIZE_MB", "1.0"))

@mcp.tool()
def read_file(path: str) -> str:
    """Reads a file from the project root with security checks."""
    try:
        p = (ROOT_DIR / path).resolve()
        
        # Security: Check path is within allowed root
        if not p.is_relative_to(ROOT_DIR): 
            logger.warning(f"Access denied for path outside root: {path}")
            return "⛔ Access Denied: Path outside project root"
        
        # Security: Reject symlinks to prevent escape
        if p.is_symlink():
            logger.warning(f"Symlink access denied: {path}")
            return "⛔ Access Denied: Symlinks not allowed"
        
        # Security: Check file size
        if p.exists() and p.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            return f"⛔ File too large (>{MAX_FILE_SIZE_MB}MB). Use external tools."
        
        return p.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return f"❌ File not found: {path}"
    except PermissionError:
        return f"❌ Permission denied: {path}"
    except Exception as e: 
        logger.error(f"Error reading file '{path}': {e}")
        return f"❌ Error reading file: {e}"

@mcp.tool()
def list_directory(path: str = ".") -> str:
    """Lists files in a directory."""
    try:
        p = (ROOT_DIR / path).resolve()
        
        # Security: Check path is within allowed root
        if not p.is_relative_to(ROOT_DIR): 
            logger.warning(f"Access denied for path outside root: {path}")
            return "⛔ Access Denied: Path outside project root"
        
        # Security: Reject symlinks to prevent escape
        if p.is_symlink():
            logger.warning(f"Symlink access denied: {path}")
            return "⛔ Access Denied: Symlinks not allowed"
        
        if not p.exists():
            return f"❌ Directory not found: {path}"
        
        if not p.is_dir():
            return f"❌ Not a directory: {path}"
        
        out = []
        with os.scandir(p) as it:
            for e in it:
                if not e.name.startswith("."): out.append(e.name)
        return "\n".join(out) if out else "(empty directory)"
    except PermissionError:
        return f"❌ Permission denied: {path}"
    except Exception as e: 
        logger.error(f"Error listing directory '{path}': {e}")
        return f"❌ Error: {e}"


@mcp.tool()
async def reload_config() -> str:
    """
    Hot-reloads upstream server configuration without restart.
    Clears existing tool registry and rebuilds from current config.
    """
    global TOOL_REGISTRY
    
    logger.info("Hot-reload requested: Clearing tool registry...")
    
    # Clear registry
    old_count = len(TOOL_REGISTRY)
    TOOL_REGISTRY = {}
    
    # Close existing sessions gracefully
    try:
        for server_name in list(manager.sessions.keys()):
            logger.debug(f"Closing session to '{server_name}'")
        manager.sessions.clear()
    except Exception as e:
        logger.warning(f"Error clearing sessions: {e}")
    
    # Rebuild registry
    await _build_registry()
    
    new_count = len(TOOL_REGISTRY)
    
    return (
        f"✅ Configuration reloaded!\n"
        f"   Previous tools: {old_count}\n"
        f"   Current tools:  {new_count}\n"
        f"   Available now:  {', '.join(list(TOOL_REGISTRY.keys())[:10])}"
        + (f"... and {new_count - 10} more" if new_count > 10 else "")
    )


@mcp.tool()
def clear_cache() -> str:
    """
    Clears all cached tool results.
    Use this when you need fresh data from upstream servers.
    """
    count = cache.clear()
    logger.info(f"Cache cleared by user request: {count} entries")
    return f"✅ Cache cleared! {count} entries removed."


@mcp.tool()
def cache_stats() -> str:
    """
    Returns current cache statistics.
    Shows hit rate, size, and recent entries.
    """
    stats = cache.get_stats()
    
    lines = [
        "📊 Cache Statistics",
        "─" * 30,
        f"📦 Size: {stats['size']}/{stats['max_size']}",
        f"⏱️  TTL: {stats['ttl_seconds']}s",
        f"✅ Hits: {stats['hits']}",
        f"❌ Misses: {stats['misses']}",
        f"📈 Hit Rate: {stats['hit_rate_percent']}%",
    ]
    
    if stats['entries']:
        lines.append("\n🔧 Recent Entries:")
        for entry in stats['entries']:
            lines.append(f"   └─ {entry['tool']}: {entry['hit_count']} hits ({entry['age_seconds']}s ago)")
    
    return "\n".join(lines)