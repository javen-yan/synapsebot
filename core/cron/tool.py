from typing import Dict, Any, Optional
import json
import time
from core.cron.service import CronService
from core.cron.models import CronJobCreate, CronJobPatch, ScheduleType, PayloadType

CRON_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string", 
            "enum": ["add", "list", "remove", "update", "status"],
            "description": "The action to perform."
        },
        "job_id": {
            "type": "string",
            "description": "ID of the job (required for remove, update)"
        },
        "job": {
            "type": "object",
            "description": "Job definition (required for add)",
            "properties": {
                "name": {"type": "string"},
                "schedule": {
                    "type": "object",
                    "description": "Schedule configuration. One of: {kind:'at', delaySeconds:..}, {kind:'at', atMs:..}, {kind:'every', everyMs:..}, {kind:'cron', expr:..}",
                    "required": ["kind"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["at", "every", "cron"]},
                        "delaySeconds": {"type": "integer", "description": "Run in X seconds from now (preferred for relative time)"},
                        "atMs": {"type": "integer"},
                        "everyMs": {"type": "integer"},
                        "expr": {"type": "string"}
                    }
                },
                "payload": {
                    "type": "object",
                    "description": "Payload to execute.",
                    "required": ["kind"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["systemEvent", "agentTurn"]},
                        "text": {"type": "string", "description": "For systemEvent"},
                        "message": {"type": "string", "description": "For agentTurn"}
                    }
                },
                "sessionTarget": {"type": "string", "enum": ["main", "isolated"]},
                "enabled": {"type": "boolean"}
            },
            "required": ["schedule", "payload"]
        },
        "patch": {
            "type": "object",
            "description": "Fields to update (for update action)"
        }
    },
    "required": ["action"]
}

class CronTool:
    def __init__(self, service: CronService):
        self.service = service

    async def __call__(self, args: Dict[str, Any]) -> str:
        action = args.get("action")
        
        if action == "status":
            jobs = self.service.list_jobs(include_disabled=True)
            return json.dumps({
                "status": "running", 
                "job_count": len(jobs),
                "running": self.service.scheduler.running
            }, default=str)

        elif action == "list":
            jobs = self.service.list_jobs(include_disabled=True)
            return json.dumps([j.model_dump() for j in jobs], default=str)

        elif action == "add":
            job_data = args.get("job")
            if not job_data:
                return "Error: 'job' argument is required for 'add' action"
            try:
                # Handle delaySeconds for relative scheduling
                schedule = job_data.get("schedule", {})
                if schedule.get("kind") == "at" and "delaySeconds" in schedule:
                    delay = schedule.pop("delaySeconds")
                    now_ms = int(time.time() * 1000)
                    schedule["atMs"] = now_ms + (delay * 1000)
                
                # Check for "atMs" is missing/invalid if delaySeconds wasn't used
                if schedule.get("kind") == "at" and "atMs" not in schedule:
                     # Check if user tried to pass atMs as small integer? 
                     # Actually if LLM passed atMs=10000, we can detect reasonable bounds.
                     # But safer to prefer delaySeconds explicitly.
                     pass 

                # Auto-populate agentId from context if available
                ctx = args.get("_context", {})
                if "agentId" not in job_data and "agent_id" in ctx:
                    job_data["agentId"] = ctx["agent_id"]

                # Auto-populate meta from context if available
                if "meta" not in job_data and "meta" in ctx:
                    job_data["meta"] = ctx["meta"]

                # Validate inputs manually if needed or let Pydantic handle it
                create_params = CronJobCreate(**job_data)
                job = await self.service.add_job(create_params)
                return f"Job added successfully. ID: {job.id}"
            except Exception as e:
                return f"Error adding job: {e}"

        elif action == "remove":
            job_id = args.get("job_id")
            if not job_id:
                return "Error: 'job_id' is required for 'remove' action"
            success = await self.service.remove_job(job_id)
            if success:
                return f"Job {job_id} removed."
            else:
                return f"Job {job_id} not found."

        elif action == "update":
            job_id = args.get("job_id")
            patch_data = args.get("patch")
            if not job_id or not patch_data:
                return "Error: 'job_id' and 'patch' are required for 'update' action"
            try:
                patch = CronJobPatch(**patch_data)
                job = await self.service.update_job(job_id, patch)
                if job:
                    return f"Job {job_id} updated."
                else:
                    return f"Job {job_id} not found."
            except Exception as e:
                return f"Error updating job: {e}"

        return f"Unknown action: {action}"
