"""Tests for Dashboard - metrics and statistics tracking."""
import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestDashboardInit:
    """Test suite for Dashboard initialization."""
    
    def test_default_stats_structure(self):
        """Should initialize with correct default structure."""
        from mcpv.dashboard import Dashboard
        
        with patch('mcpv.dashboard.STATS_FILE', Path('/fake/path/stats.json')):
            dash = Dashboard()
            
            assert "tokens_saved" in dash.stats
            assert "requests_blocked" in dash.stats
            assert "tool_calls" in dash.stats
            assert "server_latencies" in dash.stats
            assert "session_start" in dash.stats
            assert "last_updated" in dash.stats
    
    def test_load_stats_from_file(self, tmp_path):
        """Should load existing stats from disk."""
        stats_file = tmp_path / "stats.json"
        saved_stats = {
            "tokens_saved": 50000,
            "requests_blocked": 5,
            "tool_calls": {},
            "server_latencies": {},
            "session_start": "2024-01-01T00:00:00",
            "last_updated": "2024-01-01T00:00:00"
        }
        stats_file.write_text(json.dumps(saved_stats))
        
        with patch('mcpv.dashboard.STATS_FILE', stats_file):
            from mcpv.dashboard import Dashboard
            dash = Dashboard()
            
            assert dash.stats["tokens_saved"] == 50000
            assert dash.stats["requests_blocked"] == 5


class TestDashboardLogging:
    """Test suite for logging functionality."""
    
    def test_log_blocked_request_increments_counters(self, tmp_path):
        """Should increment counters when logging blocked request."""
        stats_file = tmp_path / "stats.json"
        
        with patch('mcpv.dashboard.STATS_FILE', stats_file):
            from mcpv.dashboard import Dashboard
            dash = Dashboard()
            
            initial_blocked = dash.stats["requests_blocked"]
            initial_saved = dash.stats["tokens_saved"]
            
            dash.log_blocked_request(tokens_saved=5000)
            
            assert dash.stats["requests_blocked"] == initial_blocked + 1
            assert dash.stats["tokens_saved"] == initial_saved + 5000
    
    def test_log_tool_call_tracks_usage(self, tmp_path):
        """Should track tool usage counts."""
        stats_file = tmp_path / "stats.json"
        
        with patch('mcpv.dashboard.STATS_FILE', stats_file):
            from mcpv.dashboard import Dashboard
            dash = Dashboard()
            
            dash.log_tool_call("query-docs", "context7", 150.0, success=True)
            dash.log_tool_call("query-docs", "context7", 200.0, success=True)
            
            assert dash.stats["tool_calls"]["query-docs"]["count"] == 2
            assert dash.stats["tool_calls"]["query-docs"]["errors"] == 0
    
    def test_log_tool_call_tracks_errors(self, tmp_path):
        """Should track error counts for tools."""
        stats_file = tmp_path / "stats.json"
        
        with patch('mcpv.dashboard.STATS_FILE', stats_file):
            from mcpv.dashboard import Dashboard
            dash = Dashboard()
            
            dash.log_tool_call("failing-tool", "server", 100.0, success=False)
            
            assert dash.stats["tool_calls"]["failing-tool"]["errors"] == 1
    
    def test_log_tool_call_calculates_rolling_average(self, tmp_path):
        """Should calculate rolling average latency."""
        stats_file = tmp_path / "stats.json"
        
        with patch('mcpv.dashboard.STATS_FILE', stats_file):
            from mcpv.dashboard import Dashboard
            dash = Dashboard()
            
            dash.log_tool_call("tool1", "server1", 100.0, success=True)
            dash.log_tool_call("tool2", "server1", 200.0, success=True)
            
            # Rolling average: (100 + 200) / 2 = 150
            assert dash.stats["server_latencies"]["server1"]["avg_ms"] == 150.0
            assert dash.stats["server_latencies"]["server1"]["count"] == 2


class TestDashboardSummary:
    """Test suite for summary generation."""
    
    def test_get_summary_returns_correct_keys(self, tmp_path):
        """Should return summary with all expected keys."""
        stats_file = tmp_path / "stats.json"
        
        with patch('mcpv.dashboard.STATS_FILE', stats_file):
            from mcpv.dashboard import Dashboard
            dash = Dashboard()
            
            summary = dash.get_summary()
            
            assert "tokens_saved" in summary
            assert "requests_blocked" in summary
            assert "total_tool_calls" in summary
            assert "unique_tools_used" in summary
            assert "servers_connected" in summary
    
    def test_format_status_returns_string(self, tmp_path):
        """Should return formatted string for CLI."""
        stats_file = tmp_path / "stats.json"
        
        with patch('mcpv.dashboard.STATS_FILE', stats_file):
            from mcpv.dashboard import Dashboard
            dash = Dashboard()
            
            status = dash.format_status()
            
            assert isinstance(status, str)
            assert "Statistics" in status


class TestDashboardReset:
    """Test suite for reset functionality."""
    
    def test_reset_clears_all_stats(self, tmp_path):
        """Should reset all statistics to defaults."""
        stats_file = tmp_path / "stats.json"
        
        with patch('mcpv.dashboard.STATS_FILE', stats_file):
            from mcpv.dashboard import Dashboard
            dash = Dashboard()
            
            # Add some data
            dash.log_blocked_request()
            dash.log_tool_call("tool", "server", 100.0)
            
            # Reset
            dash.reset()
            
            assert dash.stats["tokens_saved"] == 0
            assert dash.stats["requests_blocked"] == 0
            assert dash.stats["tool_calls"] == {}
            assert dash.stats["server_latencies"] == {}
    
    def test_reset_persists_to_disk(self, tmp_path):
        """Should persist reset stats to file."""
        stats_file = tmp_path / "stats.json"
        
        with patch('mcpv.dashboard.STATS_FILE', stats_file):
            from mcpv.dashboard import Dashboard
            dash = Dashboard()
            
            dash.log_blocked_request()
            dash.reset()
            
            # Reload from disk
            saved = json.loads(stats_file.read_text())
            assert saved["tokens_saved"] == 0
