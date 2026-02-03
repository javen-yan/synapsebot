from typing import Dict, Any
import json
from core.plugins.memory.manager import MemoryManager
from core.plugins.cron.models import ScheduleType # Just in case we need types later, but not strictly needed here

MEMORY_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["get", "save", "search"],
            "description": "The action to perform."
        },
        "user_id": {
            "type": "string",
            "description": "User identifier (optional, defaults to current user)"
        },
        "content": {
            "type": "string",
            "description": "Content to save (required for save)"
        },
        "query": {
            "type": "string",
            "description": "Search query (required for search)"
        }
    },
    "required": ["action"]
}

class MemoryTool:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager

    async def __call__(self, args: Dict[str, Any]) -> str:
        action = args.get("action")
        
        # Context injection
        ctx = args.get("_context", {})
        agent_id = ctx.get("agent_id", "")
        
        # Determine user_id
        # If agent_id is "channel:user_id", we can parse it.
        # Or we rely on explicit user_id arg, falling back to parsed.
        user_id = args.get("user_id")
        channel = "unknown"
        
        if agent_id:
             if ":" in agent_id:
                 id_channel, id_user = agent_id.split(":", 1)
                 channel = id_channel
                 # Only use id_user if user_id arg is NOT provided
                 if not user_id:
                     user_id = id_user
             else:
                 if not user_id:
                     user_id = agent_id
        
        if not user_id:
            return "Error: Could not determine user_id from context or arguments."

        if action == "get":
            # Just read the whole memory file
            # Ideally we might want a limit or summary
            content = await self.memory_manager.get_memory(channel, user_id)
            if not content:
                return "Memory is empty."
            return content

        elif action == "save":
            content = args.get("content")
            if not content:
                return "Error: 'content' is required for 'save' action"
            
            await self.memory_manager.save_interaction(
                channel, user_id, 
                user_msg=f"[Memory Tool Note]", 
                agent_response=content
            )
            return "Memory saved."
            
        elif action == "search":
            # Simple substring search for now as MemoryManager doesn't support vector search yet
            query = args.get("query")
            if not query:
                 return "Error: 'query' is required for 'search' action"
            
            content = await self.memory_manager.get_memory(channel, user_id)
            if not content:
                return "Memory is empty."
            
            # Simple grep-like search
            lines = content.split('\n')
            matches = []
            for i, line in enumerate(lines):
                if query.lower() in line.lower():
                    # Get context
                    start = max(0, i-1)
                    end = min(len(lines), i+2)
                    matches.append('\n'.join(lines[start:end]))
            
            if not matches:
                return f"No matches found for '{query}'"
            
            return "\n---\n".join(matches)

        return f"Unknown action: {action}"
