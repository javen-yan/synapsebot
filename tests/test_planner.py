import pytest
from unittest.mock import MagicMock
from core.plugins.planner.plugin import PlannerPlugin

def test_planner_lifecycle():
    plugin = PlannerPlugin()
    session_id = "test:123"
    
    # Context Mock
    context = {"agent_id": session_id}
    
    # 1. Create Plan
    args = {
        "_context": context,
        "goal": "Test Goal",
        "steps": ["Step 1", "Step 2"]
    }
    result = plugin.planner_tools.create_plan(args)
    assert "Plan Created" in result
    
    # 2. Verify Context Injection
    # Mock Request
    request = MagicMock()
    request.source = "test"
    request.chat_id = "123"
    
    # Need to run async method
    import asyncio
    
    ctx_text = plugin.planner_tools.get_plan(session_id)
    assert "Step 1" in ctx_text
    assert "[ ]" in ctx_text  # Pending icon
    
    # 3. Update Plan
    args_update = {
        "_context": context,
        "step_id": 1,
        "status": "done",
        "result": "Success"
    }
    plugin.planner_tools.update_plan(args_update)
    
    ctx_text_2 = plugin.planner_tools.get_plan(session_id)
    assert "[x] Step 1" in ctx_text_2
    assert "Result: Success" in ctx_text_2
