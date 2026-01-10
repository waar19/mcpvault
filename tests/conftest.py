# pytest configuration
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def temp_config_dir(tmp_path):
    """Creates a temporary config directory for testing."""
    config_dir = tmp_path / ".gemini" / "antigravity"
    config_dir.mkdir(parents=True)
    return config_dir

@pytest.fixture
def mock_session():
    """Creates a mock MCP session."""
    session = AsyncMock()
    session.list_tools = AsyncMock(return_value=MagicMock(tools=[]))
    session.call_tool = AsyncMock(return_value=MagicMock(content=[]))
    session.initialize = AsyncMock()
    return session

@pytest.fixture
def sample_config():
    """Sample MCP config for testing."""
    return {
        "mcpServers": {
            "test-server": {
                "command": "echo",
                "args": ["hello"],
                "env": {}
            }
        }
    }
