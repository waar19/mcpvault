"""MCP Vault CLI - Commands for managing mcpv."""
import typer
import asyncio
import json
from pathlib import Path
from .vault import manager, CONFIG_FILE, ROOT_PATH_FILE, BACKUP_FILE
from .server import mcp
from .dashboard import dashboard

app = typer.Typer(help="MCP Vault: Performance booster for AI agents")


@app.command()
def install(
    force: bool = typer.Option(False, "--force", "-f", help="Force install even if MCP servers exist.")
):
    """Installs mcpv as the primary gateway in Antigravity."""
    print("🛡️  Installing MCP Vault...")
    manager.install(force=force)
    print("👉 Check the output above.")


@app.command()
def start():
    """Starts the mcpv server (Used internally by Antigravity)."""
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.run(manager.cleanup())


@app.command()
def status():
    """Shows mcpv installation status and statistics."""
    print("\n🛡️ MCP Vault Status")
    print("─" * 40)
    
    # Installation status
    installed = CONFIG_FILE.exists()
    print(f"📦 Installed:          {'✅ Yes' if installed else '❌ No'}")
    
    # Root path
    if ROOT_PATH_FILE.exists():
        root = ROOT_PATH_FILE.read_text(encoding="utf-8").strip()
        print(f"📍 Locked Root:        {root}")
    else:
        print("📍 Locked Root:        Not set")
    
    # Upstream servers
    if BACKUP_FILE.exists():
        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            servers = list(config.get("mcpServers", {}).keys())
            active = [s for s, v in config.get("mcpServers", {}).items() if not v.get("disabled")]
            print(f"🌐 Upstream Servers:   {len(servers)} ({len(active)} active)")
            for s in servers[:5]:  # Show max 5
                status_icon = "🟢" if s in active else "🔴"
                print(f"   {status_icon} {s}")
            if len(servers) > 5:
                print(f"   ... and {len(servers) - 5} more")
        except Exception:
            print("🌐 Upstream Servers:   Error reading config")
    else:
        print("🌐 Upstream Servers:   None (vault empty)")
    
    # Dashboard stats
    print()
    print(dashboard.format_status())


@app.command()
def reset_stats():
    """Resets the dashboard statistics."""
    dashboard.reset()
    print("✅ Statistics reset successfully.")


if __name__ == "__main__":
    app()
