import json
import sys
import shutil
import os
import logging
import asyncio
from pathlib import Path
from typing import Optional
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

# [Import compatibility handling]
try:
    from mcp.types import StdioServerParameters
except ImportError:
    try:
        from mcp import StdioServerParameters
    except ImportError:
        from typing import Any
        StdioServerParameters = Any

# Configurable settings via environment variables
CONNECTION_TIMEOUT = float(os.environ.get("MCPV_CONNECTION_TIMEOUT", "10.0"))
MAX_RETRIES = int(os.environ.get("MCPV_MAX_RETRIES", "3"))
RETRY_DELAY = float(os.environ.get("MCPV_RETRY_DELAY", "1.0"))

# Logger setup
logger = logging.getLogger("mcpv-vault")

# Platform detection
import platform
CURRENT_PLATFORM = platform.system()  # 'Windows', 'Darwin', 'Linux'

# Path configuration - platform aware
HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".gemini" / "antigravity"
CONFIG_FILE = CONFIG_DIR / "mcp_config.json"
BACKUP_FILE = CONFIG_DIR / "mcp_config.original.json"
ROOT_PATH_FILE = CONFIG_DIR / "root_path.txt"
MY_SERVER_NAME = "mcpv-proxy"

# Antigravity paths - platform specific
def _get_antigravity_paths() -> tuple[Path, Path, Path]:
    """Returns (antigravity_dir, antigravity_exe, booster_script) for current platform."""
    if CURRENT_PLATFORM == "Windows":
        localappdata = os.environ.get("LOCALAPPDATA", str(HOME_DIR / "AppData" / "Local"))
        base = Path(localappdata) / "Programs" / "Antigravity"
        return base, base / "Antigravity.exe", CONFIG_DIR / "boost_launcher.bat"
    elif CURRENT_PLATFORM == "Darwin":  # macOS
        base = Path("/Applications/Antigravity.app/Contents/MacOS")
        return base, base / "Antigravity", CONFIG_DIR / "boost_launcher.sh"
    else:  # Linux
        base = HOME_DIR / ".local" / "share" / "antigravity"
        return base, base / "antigravity", CONFIG_DIR / "boost_launcher.sh"

ANTIGRAVITY_PATH, ANTIGRAVITY_EXE, BOOSTER_SCRIPT = _get_antigravity_paths()


def _get_desktop_path() -> Path:
    """Gets the real desktop path, handling OneDrive redirection on Windows."""
    if CURRENT_PLATFORM == "Windows":
        try:
            import ctypes
            from ctypes import wintypes
            
            # CSIDL_DESKTOPDIRECTORY = 0x0010
            CSIDL_DESKTOP = 0x0010
            SHGFP_TYPE_CURRENT = 0
            
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, SHGFP_TYPE_CURRENT, buf)
            
            if buf.value:
                return Path(buf.value)
        except Exception:
            pass  # Fall back to default
    
    # Fallback for non-Windows or if API fails
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


class VaultManager:
    def __init__(self):
        self.stack = AsyncExitStack()
        self.sessions = {}

    def install(self, force: bool = False) -> None:
        """Installs mcpv: hijacks MCP config and locks project root path."""
        success = self._hijack_config(force)
        if success:
            # Step 2: Install booster script
            self._install_booster()
            print("✨ Installation & Path Lock Complete!")

    def _hijack_config(self, force: bool) -> bool:
        if not CONFIG_DIR.exists():
            try:
                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(f"Config dir creation failed: {e}")
                print(f"❌ Config dir creation failed at {CONFIG_DIR}: {e}", file=sys.stderr)
                return False

        if not CONFIG_FILE.exists():
             with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"mcpServers": {}}, f)

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: 
                config = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not load config file, using defaults: {e}")
            config = {"mcpServers": {}}

        servers = config.get("mcpServers", {})
        other_servers = {k: v for k, v in servers.items() if k != MY_SERVER_NAME}

        if other_servers and not force:
            print(f"⚠️  Existing MCP servers found: {list(other_servers.keys())}", file=sys.stderr)
            print("   Skipping installation. Use 'mcpv install --force' to override.", file=sys.stderr)
            return False

        if other_servers:
            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                json.dump({"mcpServers": other_servers}, f, indent=2)
            print(f"📦 Backup created at: {BACKUP_FILE}", file=sys.stderr)

        # [핵심] 현재 경로 저장
        current_python = sys.executable
        current_cwd = os.getcwd()
        
        print(f"🔧 Locking Project Root to: {current_cwd}")
        
        try:
            with open(ROOT_PATH_FILE, "w", encoding="utf-8") as f:
                f.write(current_cwd)
            print(f"📍 Root path saved to {ROOT_PATH_FILE}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Failed to save root path: {e}", file=sys.stderr)

        my_config = {
            "command": current_python,
            "args": ["-m", "mcpv", "start"],
            "cwd": current_cwd,
            "env": {
                "PYTHONUNBUFFERED": "1",
                "PYTHONPATH": current_cwd
            }
        }
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"mcpServers": {MY_SERVER_NAME: my_config}}, f, indent=2)
            
        print(f"🔒 Vault config updated.", file=sys.stderr)
        return True

    def _install_booster(self):
        print("🚀 Installing Booster Script...", file=sys.stderr)
        if not ANTIGRAVITY_PATH.exists():
             print(f"⚠️  Antigravity path not found. Skipping booster.", file=sys.stderr)
             return

        batch_content = f"""@echo off
set __COMPAT_LAYER=RunAsInvoker
cd /d "{ANTIGRAVITY_PATH}"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 26646 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; $env:Path = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0;' + [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User'); Start-Process -FilePath '.\\Antigravity.exe' -ArgumentList '--disable-gpu-driver-bug-workarounds --ignore-gpu-blacklist --enable-gpu-rasterization --enable-zero-copy --enable-native-gpu-memory-buffers' -WorkingDirectory '{ANTIGRAVITY_PATH}'"
exit
"""
        try:
            with open(BOOSTER_SCRIPT, "w", encoding="utf-8") as f:
                f.write(batch_content)
            self._create_shortcut_vbs(str(BOOSTER_SCRIPT), "Antigravity Boost (mcpv)", str(ANTIGRAVITY_EXE))
        except Exception as e:
            print(f"⚠️  Booster installation failed: {e}", file=sys.stderr)

    def _create_shortcut_vbs(self, target: str, name: str, icon: str):
        """Creates a desktop shortcut using VBS. Handles errors gracefully."""
        desktop = _get_desktop_path()
        
        if not desktop.exists():
            print(f"⚠️  Desktop folder not found at {desktop}", file=sys.stderr)
            return
        
        # Sanitize name to prevent path injection (only alphanumeric, spaces, parentheses)
        import re
        safe_name = re.sub(r'[^\w\s\(\)\-]', '', name)
        if not safe_name:
            print("⚠️  Invalid shortcut name after sanitization", file=sys.stderr)
            return
            
        link_path = str(desktop / f"{safe_name}.lnk")
        
        def escape_vbs_string(s: str) -> str:
            """Escape a string for safe use in VBS. Only double quotes need escaping."""
            # In VBS, only double quotes need to be doubled, backslashes are literal
            return s.replace('"', '""')
        
        target_escaped = escape_vbs_string(target)
        link_escaped = escape_vbs_string(link_path)
        icon_escaped = escape_vbs_string(icon)
        
        vbs_script = f'''On Error Resume Next
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{link_escaped}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "cmd.exe"
oLink.Arguments = "/c ""{target_escaped}"""
oLink.IconLocation = "{icon_escaped},0"
oLink.WindowStyle = 7
oLink.Save
If Err.Number <> 0 Then
    WScript.Echo "Error: " & Err.Description
End If
'''
        vbs_file = CONFIG_DIR / "create_shortcut.vbs"
        try:
            with open(vbs_file, "w", encoding="utf-8") as f: 
                f.write(vbs_script)
            result = os.system(f'cscript //nologo "{vbs_file}"')
            if result == 0:
                print(f"✅ Desktop shortcut created: {name}", file=sys.stderr)
            else:
                print(f"⚠️  Shortcut creation returned code {result}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Could not create shortcut: {e}", file=sys.stderr)
        finally:
            if vbs_file.exists(): 
                os.remove(vbs_file)

    async def get_session(self, server_name: str) -> Optional[ClientSession]:
        """
        Gets or creates a session to an upstream MCP server.
        Implements retry with exponential backoff for resilience.
        """
        # Return cached session if available
        if server_name in self.sessions: 
            return self.sessions[server_name]
        
        # Validate vault exists
        if not BACKUP_FILE.exists(): 
            logger.error("Vault backup file not found")
            raise FileNotFoundError("Vault is empty. Run 'mcpv install' first.")
        
        # Load config
        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f: 
                config = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to read vault config: {e}")
            raise RuntimeError(f"Could not read vault config: {e}")
        
        srv = config.get("mcpServers", {}).get(server_name)
        if not srv: 
            logger.warning(f"Server '{server_name}' not found in vault")
            raise ValueError(f"Server '{server_name}' not found in vault.")
        
        # Prepare environment
        upstream_env = os.environ.copy()
        upstream_env["CI"] = "true" 
        upstream_env.update(srv.get("env", {}))

        # Resolve command (Windows compatibility: npx -> npx.cmd)
        cmd = srv["command"]
        resolved_cmd = shutil.which(cmd)
        
        if not resolved_cmd and os.name == 'nt':
            resolved_cmd = shutil.which(f"{cmd}.cmd") or shutil.which(f"{cmd}.exe")
        
        final_cmd = resolved_cmd if resolved_cmd else cmd
        logger.debug(f"Resolved command for '{server_name}': {final_cmd}")

        params = StdioServerParameters(
            command=final_cmd,
            args=srv.get("args", []),
            env=upstream_env
        )
        
        # Retry loop with exponential backoff
        last_error: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Connecting to '{server_name}' (attempt {attempt}/{MAX_RETRIES})")
                
                read, write = await asyncio.wait_for(
                    self.stack.enter_async_context(stdio_client(params)),
                    timeout=CONNECTION_TIMEOUT
                )
                session = await self.stack.enter_async_context(ClientSession(read, write))
                await asyncio.wait_for(session.initialize(), timeout=CONNECTION_TIMEOUT)
                
                self.sessions[server_name] = session
                logger.info(f"Successfully connected to '{server_name}'")
                return session
                
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Connection to '{server_name}' timed out after {CONNECTION_TIMEOUT}s")
                logger.warning(f"Timeout connecting to '{server_name}' (attempt {attempt})")
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to connect to '{server_name}' (attempt {attempt}): {e}")
            
            # Exponential backoff before retry (except on last attempt)
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * (2 ** (attempt - 1))
                logger.debug(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        logger.error(f"Failed to connect to '{server_name}' after {MAX_RETRIES} attempts")
        raise ConnectionError(f"Could not connect to '{server_name}' after {MAX_RETRIES} attempts: {last_error}")

    async def cleanup(self):
        await self.stack.aclose()

manager = VaultManager()