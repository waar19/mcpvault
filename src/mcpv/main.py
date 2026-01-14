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


@app.command()
def uninstall():
    """Uninstalls mcpv and restores original MCP config."""
    import shutil
    import os
    
    print("🗑️  Uninstalling MCP Vault...")
    
    restored = False
    
    # 1. Restore original config
    if BACKUP_FILE.exists():
        try:
            shutil.copy(BACKUP_FILE, CONFIG_FILE)
            print("✅ Original MCP config restored.")
            restored = True
        except Exception as e:
            print(f"⚠️  Could not restore config: {e}")
    else:
        # Remove mcpv config entirely
        if CONFIG_FILE.exists():
            try:
                CONFIG_FILE.unlink()
                print("✅ MCP Vault config removed.")
            except Exception as e:
                print(f"⚠️  Could not remove config: {e}")
    
    # 2. Remove root path file
    if ROOT_PATH_FILE.exists():
        try:
            ROOT_PATH_FILE.unlink()
            print("✅ Root path lock removed.")
        except Exception as e:
            print(f"⚠️  Could not remove root path: {e}")
    
    # 3. Remove desktop shortcut
    # Use Windows Shell API to get real desktop path (handles OneDrive redirection)
    import platform
    if platform.system() == "Windows":
        try:
            import ctypes
            from ctypes import wintypes
            CSIDL_DESKTOP = 0x0010
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, 0, buf)
            desktop = Path(buf.value) if buf.value else Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        except Exception:
            desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
    else:
        desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
    
    shortcut = desktop / "Antigravity Boost (mcpv).lnk"
    if shortcut.exists():
        try:
            shortcut.unlink()
            print("✅ Desktop shortcut removed.")
        except Exception as e:
            print(f"⚠️  Could not remove shortcut: {e}")
    
    # 4. Reset dashboard
    dashboard.reset()
    
    print("\n🏁 Uninstallation complete!")
    if restored:
        print("   Your original MCP servers are now active again.")


@app.command()
def health():
    """Shows health status of all upstream servers."""
    from .health import monitor
    print()
    print(monitor.format_status())


@app.command()
def reconnect(server_name: str = typer.Argument(None, help="Server name to reset, or 'all' for all servers")):
    """Resets circuit breaker for a server to allow reconnection."""
    from .health import monitor
    
    if server_name is None or server_name == "all":
        # Reset all servers
        status = monitor.get_all_status()
        count = 0
        for srv in status["servers"]:
            if monitor.reset_server(srv["name"]):
                count += 1
        print(f"✅ Reset {count} server circuit breakers.")
    else:
        if monitor.reset_server(server_name):
            print(f"✅ Circuit breaker reset for '{server_name}'.")
        else:
            print(f"⚠️  Server '{server_name}' not found in health registry.")


if __name__ == "__main__":
    app()
