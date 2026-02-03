from typing import Dict, Any, List
from core.plugins.planner.models import Plan, PlanStep

CREATE_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "goal": {"type": "string", "description": "The overall goal of this plan."},
        "steps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of step descriptions."
        }
    },
    "required": ["goal", "steps"]
}

UPDATE_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "step_id": {"type": "integer", "description": "The ID of the step to update (1-based)."},
        "status": {"type": "string", "enum": ["in_progress", "done", "failed"], "description": "New status of the step."},
        "result": {"type": "string", "description": "Optional result or output of the step."}
    },
    "required": ["step_id", "status"]
}

GET_PLAN_SCHEMA = {
    "type": "object",
    "properties": {},
    "description": "Get the current plan status."
}

class PlannerTools:
    def __init__(self):
        # In-memory storage: session_id -> Plan
        self.plans: Dict[str, Plan] = {}

    def get_plan(self, session_id: str) -> str:
        plan = self.plans.get(session_id)
        if not plan:
            return "No active plan found."
        
        output = f"## Current Plan: {plan.goal} (Status: {plan.status})\n"
        for step in plan.steps:
            icon = "[ ]"
            if step.status == "in_progress": icon = "[/]"
            elif step.status == "done": icon = "[x]"
            elif step.status == "failed": icon = "[!]"
            
            output += f"{step.id}. {icon} {step.description}\n"
            if step.result:
                output += f"   Result: {step.result}\n"
        
        return output

    def create_plan(self, args: Dict[str, Any]) -> str:
        context = args.get("_context", {})
        session_id = context.get("agent_id", "unknown")
        
        goal = args.get("goal")
        step_descs = args.get("steps", [])
        
        steps = []
        for i, desc in enumerate(step_descs, 1):
            steps.append(PlanStep(id=i, description=desc))
            
        plan = Plan(goal=goal, steps=steps)
        self.plans[session_id] = plan
        
        # Return the plan text so the Agent can show it immediately
        plan_text = self.get_plan(session_id)
        return f"Plan Created.\n{plan_text}\n[Instruction] You MUST now present this plan to the user."

    def update_plan(self, args: Dict[str, Any]) -> str:
        context = args.get("_context", {})
        session_id = context.get("agent_id", "unknown")
        
        plan = self.plans.get(session_id)
        if not plan:
            return "Error: No active plan found."
            
        step_id = args.get("step_id")
        status = args.get("status")
        result = args.get("result")
        
        if plan.update_step(step_id, status, result):
            msg = f"Step {step_id} updated to {status}."
            if result:
                 msg += f" Result: {result}"
            
            if plan.status == "done":
                 msg += "\n[Instruction] Plan Completed! You MUST provide a final summary to the user now."
            else:
                 msg += "\n[Instruction] You MUST inform the user of this step completion and what you will do next."
            return msg
        else:
            return f"Error: Step {step_id} not found."
