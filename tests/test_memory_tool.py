import pytest
import asyncio
from pathlib import Path
from core.plugins.memory.tool import MemoryTool
from core.plugins.memory.manager import MemoryManager

# Mock MemoryManager
class MockMemoryManager:
    def __init__(self):
        self.memory = {}

    async def get_memory(self, channel, user_id):
        return self.memory.get(f"{channel}:{user_id}", "")

    async def save_interaction(self, channel, user_id, user_msg, agent_response):
        key = f"{channel}:{user_id}"
        if key not in self.memory:
            self.memory[key] = ""
        self.memory[key] += f"\nUser: {user_msg}\nAssistant: {agent_response}\n"

@pytest.mark.asyncio
async def test_memory_tool_get_save_search():
    mock_manager = MockMemoryManager()
    tool = MemoryTool(mock_manager)
    
    # Test Save
    save_args = {
        "action": "save",
        "content": "This is a test note.",
        "_context": {"agent_id": "test_channel:user123"}
    }
    result = await tool(save_args)
    assert result == "Memory saved."
    assert "This is a test note" in mock_manager.memory["test_channel:user123"]

    # Test Get
    get_args = {
        "action": "get",
        "_context": {"agent_id": "test_channel:user123"}
    }
    result = await tool(get_args)
    assert "This is a test note" in result

    # Test Search
    search_args = {
        "action": "search",
        "query": "test",
        "_context": {"agent_id": "test_channel:user123"}
    }
    result = await tool(search_args)
    assert "This is a test note" in result
    
    # Test Search No Match
    search_args_fail = {
        "action": "search",
        "query": "banana",
        "_context": {"agent_id": "test_channel:user123"}
    }
    result = await tool(search_args_fail)
    assert "No matches found" in result

@pytest.mark.asyncio
async def test_memory_tool_context_resolution():
    mock_manager = MockMemoryManager()
    tool = MemoryTool(mock_manager)
    
    # Test basic resolution
    save_args = {
        "action": "save",
        "content": "context test",
        "_context": {"agent_id": "slack:U888"}
    }
    await tool(save_args)
    assert "context test" in mock_manager.memory["slack:U888"]
    
    # Test override
    save_args_override = {
        "action": "save",
        "content": "override test",
        "user_id": "U999",
        "_context": {"agent_id": "slack:U888"} # Should be ignored for user_id part if we assume channel stickiness?
        # Actually logic is: if user_id arg provided, use it. channel is unknown/default unless parsed from somewhere?
        # My impl: channel "unknown" if parsing fails, but here agent_id has channel. 
        # But if user_id arg provided, I didn't verify channel updates.
        # Let's check impl: 
        # if ":" in agent_id: channel, _ = agent_id.split(":", 1)
        # user_id = args.get("user_id") (Overrides parsed user_id)
        # So it uses channel from context, but user_id from arg. Correct.
    }
    await tool(save_args_override)
    # user_id overridden to U999, channel kept as slack
    assert "override test" in mock_manager.memory["slack:U999"]

