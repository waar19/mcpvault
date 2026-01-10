"""Dashboard for tracking mcpv metrics and statistics."""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("mcpv-dashboard")

# Stats file location
STATS_FILE = Path.home() / ".gemini" / "antigravity" / "mcpv_stats.json"

# Estimated tokens saved per blocked context request
TOKENS_PER_CONTEXT = 10000


class Dashboard:
    """Tracks and persists mcpv usage statistics."""
    
    def __init__(self):
        self.stats: Dict[str, Any] = {
            "tokens_saved": 0,
            "requests_blocked": 0,
            "tool_calls": {},
            "server_latencies": {},
            "session_start": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        self._load_stats()
    
    def _load_stats(self) -> None:
        """Load existing stats from disk."""
        try:
            if STATS_FILE.exists():
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    # Merge with defaults (keep new keys)
                    self.stats.update(saved)
                logger.debug(f"Loaded stats from {STATS_FILE}")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not load stats: {e}")
    
    def _save_stats(self) -> None:
        """Persist stats to disk."""
        try:
            self.stats["last_updated"] = datetime.now().isoformat()
            STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2)
        except OSError as e:
            logger.warning(f"Could not save stats: {e}")
    
    def log_blocked_request(self, tokens_saved: int = TOKENS_PER_CONTEXT) -> None:
        """Record a blocked context request."""
        self.stats["requests_blocked"] += 1
        self.stats["tokens_saved"] += tokens_saved
        self._save_stats()
        logger.info(f"Blocked request #{self.stats['requests_blocked']}, saved ~{tokens_saved} tokens")
    
    def log_tool_call(self, tool_name: str, server: str, latency_ms: float, success: bool = True) -> None:
        """Record a tool execution."""
        # Track tool usage count
        if tool_name not in self.stats["tool_calls"]:
            self.stats["tool_calls"][tool_name] = {"count": 0, "errors": 0}
        
        self.stats["tool_calls"][tool_name]["count"] += 1
        if not success:
            self.stats["tool_calls"][tool_name]["errors"] += 1
        
        # Track server latency (rolling average)
        if server not in self.stats["server_latencies"]:
            self.stats["server_latencies"][server] = {"avg_ms": 0, "count": 0}
        
        srv_stats = self.stats["server_latencies"][server]
        srv_stats["count"] += 1
        # Running average calculation
        srv_stats["avg_ms"] = srv_stats["avg_ms"] + (latency_ms - srv_stats["avg_ms"]) / srv_stats["count"]
        
        self._save_stats()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current statistics."""
        return {
            "tokens_saved": self.stats["tokens_saved"],
            "requests_blocked": self.stats["requests_blocked"],
            "total_tool_calls": sum(t["count"] for t in self.stats["tool_calls"].values()),
            "unique_tools_used": len(self.stats["tool_calls"]),
            "servers_connected": len(self.stats["server_latencies"]),
            "avg_latencies": {
                s: f"{v['avg_ms']:.1f}ms" 
                for s, v in self.stats["server_latencies"].items()
            },
            "session_start": self.stats.get("session_start", "unknown")
        }
    
    def format_status(self) -> str:
        """Format stats for CLI display."""
        summary = self.get_summary()
        
        lines = [
            "📊 MCP Vault Statistics",
            "─" * 40,
            f"🛡️  Tokens Saved:       ~{summary['tokens_saved']:,}",
            f"🚫 Requests Blocked:   {summary['requests_blocked']}",
            f"🔧 Total Tool Calls:   {summary['total_tool_calls']}",
            f"📦 Unique Tools Used:  {summary['unique_tools_used']}",
            f"🌐 Servers Connected:  {summary['servers_connected']}",
        ]
        
        if summary["avg_latencies"]:
            lines.append("\n⏱️  Server Latencies:")
            for server, latency in summary["avg_latencies"].items():
                lines.append(f"   └─ {server}: {latency}")
        
        return "\n".join(lines)
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.stats = {
            "tokens_saved": 0,
            "requests_blocked": 0,
            "tool_calls": {},
            "server_latencies": {},
            "session_start": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        self._save_stats()
        logger.info("Dashboard stats reset")


# Singleton instance
dashboard = Dashboard()
