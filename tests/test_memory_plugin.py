import pytest
from unittest.mock import AsyncMock, MagicMock
from core.plugins.memory.plugin import MemoryPlugin
from core.eventbus import EventBus, BotResponse

@pytest.fixture
def mock_context():
    context = MagicMock()
    context.config.storage.memory_enabled = True
    context.config.storage.get_memory_path = "/tmp/memory"
    context.event_bus = AsyncMock(spec=EventBus)
    return context

@pytest.fixture
def memory_plugin(mock_context):
    plugin = MemoryPlugin(mock_context)
    plugin.manager = AsyncMock() # Mock the internal manager
    return plugin

@pytest.mark.asyncio
async def test_on_response_buffering(memory_plugin):
    # Simulate chunks
    req_id = "req-123"
    
    chunk1 = BotResponse(
        request_id=req_id,
        target="web",
        chat_id="user1",
        content="Hello ",
        meta={"type": "chunk"}
    )
    
    chunk2 = BotResponse(
        request_id=req_id,
        target="web",
        chat_id="user1",
        content="World",
        meta={"type": "chunk"}
    )
    
    await memory_plugin._on_response(chunk1)
    await memory_plugin._on_response(chunk2)
    
    # Verify buffer
    assert req_id in memory_plugin._buffers
    assert memory_plugin._buffers[req_id] == ["Hello ", "World"]
    
    # Simulate Done event (with empty content, relying on buffer)
    done_response = BotResponse(
        request_id=req_id,
        target="web",
        chat_id="user1",
        content="", # Empty, should use buffer
        meta={"done": True, "user_msg": "Hi bot"}
    )
    
    await memory_plugin._on_response(done_response)
    
    # Verify manager.save_interaction called with merged content
    memory_plugin.manager.save_interaction.assert_called_once_with(
        channel="web",
        user_id="user1",
        user_msg="Hi bot",
        agent_response="Hello World"
    )
    
    # Verify buffer cleared
    assert req_id not in memory_plugin._buffers

@pytest.mark.asyncio
async def test_on_response_no_chunks(memory_plugin):
    # Standard response without chunks
    response = BotResponse(
        target="web",
        chat_id="user2",
        content="Stand alone response",
        meta={"user_msg": "Question"}
    )
    
    await memory_plugin._on_response(response)
    
    memory_plugin.manager.save_interaction.assert_called_once_with(
        channel="web",
        user_id="user2",
        user_msg="Question",
        agent_response="Stand alone response"
    )
