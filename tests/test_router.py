"""Tests for Smart Router - tool resolution and auto-correction."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestToolResolution:
    """Test suite for tool name resolution."""
    
    @pytest.mark.asyncio
    async def test_exact_match_found(self):
        """Should find tool with exact name match."""
        mock_registry = {
            "query-docs": {
                "server": "context7",
                "real_name": "query-docs",
                "desc": "Query documentation",
                "args": "query"
            }
        }
        
        with patch('mcpv.server.TOOL_REGISTRY', mock_registry):
            with patch('mcpv.server.manager.get_session', new_callable=AsyncMock) as mock_session:
                mock_result = MagicMock()
                mock_result.content = [MagicMock(type="text", text="Result")]
                mock_session.return_value.call_tool = AsyncMock(return_value=mock_result)
                
                from mcpv.server import run_tool
                # FastMCP wraps functions - access the underlying function via .fn
                result = await run_tool.fn("query-docs", {"query": "test"})
                
                assert "Result" in result
    
    @pytest.mark.asyncio
    async def test_server_name_confused_as_tool(self):
        """Should detect when server name is used instead of tool name."""
        mock_registry = {
            "query-docs": {
                "server": "context7",
                "real_name": "query-docs",
                "desc": "Query documentation",
                "args": "query"
            }
        }
        
        with patch('mcpv.server.TOOL_REGISTRY', mock_registry):
            from mcpv.server import run_tool
            result = await run_tool.fn("context7", {})
            
            assert "SERVER name" in result
            assert "query-docs" in result
    
    @pytest.mark.asyncio
    async def test_typo_suggestions(self):
        """Should suggest similar tool names for typos."""
        mock_registry = {
            "query-docs": {
                "server": "context7",
                "real_name": "query-docs",
                "desc": "Query documentation",
                "args": "query"
            },
            "query-code": {
                "server": "context7",
                "real_name": "query-code",
                "desc": "Query code",
                "args": "query"
            }
        }
        
        with patch('mcpv.server.TOOL_REGISTRY', mock_registry):
            from mcpv.server import run_tool
            result = await run_tool.fn("query", {})
            
            assert "Did you mean" in result
            assert "query-docs" in result or "query-code" in result
    
    @pytest.mark.asyncio
    async def test_unknown_tool_prompts_context(self):
        """Should prompt to call get_initial_context for unknown tools."""
        mock_registry = {
            "some-tool": {
                "server": "test",
                "real_name": "some-tool",
                "desc": "Test",
                "args": ""
            }
        }
        
        with patch('mcpv.server.TOOL_REGISTRY', mock_registry):
            from mcpv.server import run_tool
            result = await run_tool.fn("completely-unknown", {})
            
            assert "get_initial_context" in result


class TestReadFileSecurity:
    """Test suite for read_file security."""
    
    def test_rejects_path_outside_root(self, tmp_path):
        """Should reject paths that escape the project root."""
        with patch('mcpv.server.ROOT_DIR', tmp_path):
            from mcpv.server import read_file
            
            result = read_file.fn("../../etc/passwd")
            
            assert "Access Denied" in result
    
    def test_rejects_symlinks(self, tmp_path):
        """Should reject symlink paths."""
        # Create a file and symlink
        real_file = tmp_path / "real.txt"
        real_file.write_text("secret")
        link = tmp_path / "link.txt"
        
        try:
            link.symlink_to(real_file)
        except OSError:
            pytest.skip("Symlinks not supported on this system")
        
        with patch('mcpv.server.ROOT_DIR', tmp_path):
            from mcpv.server import read_file
            
            result = read_file.fn("link.txt")
            
            assert "Symlinks not allowed" in result
    
    def test_reads_valid_file(self, tmp_path):
        """Should successfully read files within root."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        with patch('mcpv.server.ROOT_DIR', tmp_path):
            from mcpv.server import read_file
            
            result = read_file.fn("test.txt")
            
            assert result == "Hello, World!"
    
    def test_file_not_found(self, tmp_path):
        """Should return error for missing files."""
        with patch('mcpv.server.ROOT_DIR', tmp_path):
            from mcpv.server import read_file
            
            result = read_file.fn("nonexistent.txt")
            
            assert "File not found" in result

