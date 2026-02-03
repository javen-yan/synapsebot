from typing import List, Any
from core.plugins.base import Plugin
from core.tools import Tool
from core.plugins.planner.tools import PlannerTools, CREATE_PLAN_SCHEMA, UPDATE_PLAN_SCHEMA, GET_PLAN_SCHEMA

class PlannerPlugin(Plugin):
    """
    Planner Plugin
    
    Allows the agent to create and track plans for complex tasks.
    """
    
    def __init__(self, context: Any = None):
        super().__init__(context)
        self.planner_tools = PlannerTools()

    async def initialize(self):
        pass

    async def close(self):
        pass

    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="plan_create",
                description="Create a new plan with a list of steps.",
                input_schema=CREATE_PLAN_SCHEMA,
                handler=self.planner_tools.create_plan
            ),
            Tool(
                name="plan_update",
                description="Update the status of a plan step.",
                input_schema=UPDATE_PLAN_SCHEMA,
                handler=self.planner_tools.update_plan
            ),
            Tool(
                name="plan_get",
                description="Get the current plan status.",
                input_schema=GET_PLAN_SCHEMA,
                handler=lambda args: self.planner_tools.get_plan(
                    args.get("_context", {}).get("agent_id", "unknown")
                )
            )
        ]

    async def context_prompt(self, request: Any = None) -> str:
        """Inject current plan into context."""
        if not request:
            return ""
            
        session_id = f"{request.source}:{request.chat_id}"
        plan_text = self.planner_tools.get_plan(session_id)
        
        if "No active plan" in plan_text:
            # Encouragement to use the planner for complex tasks
            return """
[System Hints]
- For complex, multi-step tasks (e.g. extensive research, coding multiple files), you SHOULD use `plan_create` first.
- This helps you keep track of progress and ensures you don't get lost.
"""
            
        return f"\n[System: Active Plan]\n{plan_text}\n(Use `plan_update` to mark steps as done/failed.)\n[Communication Rule] Always keep the user informed after each step update.\n"
