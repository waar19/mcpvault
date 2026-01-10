"""Tests for CLI commands."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner

runner = CliRunner()


class TestInstallCommand:
    """Test suite for install command."""
    
    def test_install_calls_manager_install(self):
        """Should call manager.install with correct args."""
        with patch('mcpv.main.manager') as mock_manager:
            from mcpv.main import app
            
            result = runner.invoke(app, ["install"])
            
            mock_manager.install.assert_called_once_with(force=False)
    
    def test_install_force_flag(self):
        """Should pass force=True when --force is used."""
        with patch('mcpv.main.manager') as mock_manager:
            from mcpv.main import app
            
            result = runner.invoke(app, ["install", "--force"])
            
            mock_manager.install.assert_called_once_with(force=True)


class TestStatusCommand:
    """Test suite for status command."""
    
    def test_status_shows_installed_status(self, tmp_path):
        """Should display installation status."""
        config_file = tmp_path / "mcp_config.json"
        config_file.touch()
        
        with patch('mcpv.main.CONFIG_FILE', config_file):
            with patch('mcpv.main.ROOT_PATH_FILE', tmp_path / "nonexistent.txt"):
                with patch('mcpv.main.BACKUP_FILE', tmp_path / "nonexistent.json"):
                    with patch('mcpv.main.dashboard') as mock_dash:
                        mock_dash.format_status.return_value = "Mock Stats"
                        
                        from mcpv.main import app
                        result = runner.invoke(app, ["status"])
                        
                        assert "✅ Yes" in result.output
    
    def test_status_shows_not_installed(self, tmp_path):
        """Should show not installed when config missing."""
        with patch('mcpv.main.CONFIG_FILE', tmp_path / "nonexistent.json"):
            with patch('mcpv.main.ROOT_PATH_FILE', tmp_path / "nonexistent.txt"):
                with patch('mcpv.main.BACKUP_FILE', tmp_path / "nonexistent.json"):
                    with patch('mcpv.main.dashboard') as mock_dash:
                        mock_dash.format_status.return_value = "Mock Stats"
                        
                        from mcpv.main import app
                        result = runner.invoke(app, ["status"])
                        
                        assert "❌ No" in result.output


class TestResetStatsCommand:
    """Test suite for reset-stats command."""
    
    def test_reset_stats_calls_dashboard_reset(self):
        """Should call dashboard.reset()."""
        with patch('mcpv.main.dashboard') as mock_dash:
            from mcpv.main import app
            
            result = runner.invoke(app, ["reset-stats"])
            
            mock_dash.reset.assert_called_once()
            assert "✅" in result.output


class TestStartCommand:
    """Test suite for start command."""
    
    def test_start_runs_mcp_server(self):
        """Should run the MCP server."""
        with patch('mcpv.main.mcp') as mock_mcp:
            with patch('mcpv.main.manager') as mock_manager:
                with patch('mcpv.main.asyncio') as mock_asyncio:
                    from mcpv.main import app
                    
                    # Simulate KeyboardInterrupt to exit cleanly
                    mock_mcp.run.side_effect = KeyboardInterrupt()
                    
                    result = runner.invoke(app, ["start"])
                    
                    mock_mcp.run.assert_called_once()
