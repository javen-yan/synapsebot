from typing import List, Optional, Literal
from pydantic import BaseModel, Field
import time

PlanStatus = Literal["pending", "in_progress", "done", "failed"]

class PlanStep(BaseModel):
    id: int
    description: str
    status: PlanStatus = "pending"
    result: Optional[str] = None

class Plan(BaseModel):
    goal: str
    steps: List[PlanStep]
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    status: PlanStatus = "in_progress"

    def update_step(self, step_id: int, status: PlanStatus, result: Optional[str] = None):
        for step in self.steps:
            if step.id == step_id:
                step.status = status
                if result is not None:
                    step.result = result
                # Auto-update plan status?
                # If all done, plan is done.
                if all(s.status == "done" for s in self.steps):
                    self.status = "done"
                return True
        return False
