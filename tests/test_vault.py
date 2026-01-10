"""Tests for VaultManager - config hijacking and session management."""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestVaultConfig:
    """Test suite for vault configuration management."""
    
    def test_hijack_creates_backup_when_servers_exist(self, tmp_path, sample_config):
        """Should create backup file when existing servers are found."""
        # Setup: Create mock config directory
        with patch('mcpv.vault.CONFIG_DIR', tmp_path):
            with patch('mcpv.vault.CONFIG_FILE', tmp_path / "mcp_config.json"):
                with patch('mcpv.vault.BACKUP_FILE', tmp_path / "mcp_config.original.json"):
                    # Write initial config with servers
                    config_file = tmp_path / "mcp_config.json"
                    with open(config_file, "w") as f:
                        json.dump(sample_config, f)
                    
                    from mcpv.vault import VaultManager
                    manager = VaultManager()
                    
                    # Force install
                    with patch('mcpv.vault.ANTIGRAVITY_PATH', tmp_path):
                        manager._hijack_config(force=True)
                    
                    # Check backup was created
                    backup_file = tmp_path / "mcp_config.original.json"
                    assert backup_file.exists()
    
    def test_hijack_skips_without_force(self, tmp_path, sample_config, capsys):
        """Should skip installation if servers exist and force=False."""
        with patch('mcpv.vault.CONFIG_DIR', tmp_path):
            with patch('mcpv.vault.CONFIG_FILE', tmp_path / "mcp_config.json"):
                # Write initial config
                config_file = tmp_path / "mcp_config.json"
                with open(config_file, "w") as f:
                    json.dump(sample_config, f)
                
                from mcpv.vault import VaultManager
                manager = VaultManager()
                
                result = manager._hijack_config(force=False)
                
                assert result is False
    
    def test_root_path_saved(self, tmp_path):
        """Should save current working directory to root_path.txt."""
        with patch('mcpv.vault.CONFIG_DIR', tmp_path):
            with patch('mcpv.vault.CONFIG_FILE', tmp_path / "mcp_config.json"):
                with patch('mcpv.vault.BACKUP_FILE', tmp_path / "backup.json"):
                    with patch('mcpv.vault.ROOT_PATH_FILE', tmp_path / "root_path.txt"):
                        with patch('mcpv.vault.ANTIGRAVITY_PATH', tmp_path):
                            # Empty initial config
                            config_file = tmp_path / "mcp_config.json"
                            with open(config_file, "w") as f:
                                json.dump({"mcpServers": {}}, f)
                            
                            from mcpv.vault import VaultManager
                            manager = VaultManager()
                            manager._hijack_config(force=False)
                            
                            root_file = tmp_path / "root_path.txt"
                            assert root_file.exists()
                            assert root_file.read_text().strip() == os.getcwd()


class TestVaultConnection:
    """Test suite for upstream server connections."""
    
    @pytest.mark.asyncio
    async def test_get_session_caches_session(self, tmp_path, sample_config, mock_session):
        """Should return cached session on subsequent calls."""
        with patch('mcpv.vault.BACKUP_FILE', tmp_path / "backup.json"):
            # Write backup config
            backup = tmp_path / "backup.json"
            with open(backup, "w") as f:
                json.dump(sample_config, f)
            
            from mcpv.vault import VaultManager
            manager = VaultManager()
            
            # Pre-populate cache
            manager.sessions["test-server"] = mock_session
            
            result = await manager.get_session("test-server")
            
            assert result is mock_session
    
    @pytest.mark.asyncio
    async def test_get_session_raises_on_missing_server(self, tmp_path):
        """Should raise ValueError for unknown server."""
        with patch('mcpv.vault.BACKUP_FILE', tmp_path / "backup.json"):
            backup = tmp_path / "backup.json"
            with open(backup, "w") as f:
                json.dump({"mcpServers": {}}, f)
            
            from mcpv.vault import VaultManager
            manager = VaultManager()
            
            with pytest.raises(ValueError, match="not found"):
                await manager.get_session("nonexistent-server")
    
    @pytest.mark.asyncio
    async def test_get_session_raises_on_empty_vault(self, tmp_path):
        """Should raise FileNotFoundError if vault is empty."""
        with patch('mcpv.vault.BACKUP_FILE', tmp_path / "nonexistent.json"):
            from mcpv.vault import VaultManager
            manager = VaultManager()
            
            with pytest.raises(FileNotFoundError, match="Vault is empty"):
                await manager.get_session("any-server")
