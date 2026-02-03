from typing import List, Any
from core.eventbus import BotResponse, BotRequest
from core.plugins.base import Plugin
from core.tools import Tool
from core.plugins.memory.tool import MemoryTool, MEMORY_TOOL_SCHEMA
from core.plugins.memory.manager import MemoryManager

class MemoryPlugin(Plugin):
    def __init__(self, context: Any = None):
        super().__init__(context)
        self.manager = None
        self.tool = None
        self._buffers = {} # request_id -> list of chunks

    async def initialize(self):
        config = self.context.config
        # logic from dispatcher: self.memory_manager = MemoryManager(config.storage.get_memory_path)
        self.manager = MemoryManager(config.storage.get_memory_path)
        self.tool = MemoryTool(self.manager)
        # Subscribe to response events for auto-saving
        if config.storage.memory_enabled:
             self.context.event_bus.subscribe("agent:response", self._on_response)

    async def _on_response(self, response: BotResponse):
        is_chunk = response.meta.get("type") == "chunk"
        req_id = response.request_id or response.id
        
        if is_chunk:
            if req_id not in self._buffers:
                self._buffers[req_id] = []
            self._buffers[req_id].append(response.content)
            return

        is_done = response.meta.get("done", False)
        # If it's a final response (done=True) or just a standard response
        # We should save it.
        
        # If we have buffered chunks, use them if content is empty?
        # Dispatcher sends full content in done event, but user requested we merge chunks.
        # Let's support both.
        
        full_content = response.content
        if not full_content and req_id in self._buffers:
             full_content = "".join(self._buffers[req_id])
        
        # Cleanup buffer
        if req_id in self._buffers:
             del self._buffers[req_id]

        if not full_content:
            return

        user_msg = response.meta.get("user_msg", "")
        if user_msg:
             await self.manager.save_interaction(
                channel=response.target,
                user_id=response.chat_id,
                user_msg=user_msg,
                agent_response=full_content
            )

    async def context_prompt(self, request: BotRequest = None) -> str:
        if not request or not self.manager:
            return ""
            
        # Get memory summary
        user_memory = await self.manager.get_memory_summary(
            channel=request.source,
            user_id=request.chat_id,
            max_length=self.context.config.storage.memory_max_context
        )
        
        if user_memory:
            return f"\n\n## User Memory\n{user_memory}\n"
        return ""

    def get_tools(self) -> List[Tool]:
        if not self.tool:
            return []
            
        return [
            Tool(
                name="memory",
                description="Manage user memory (get string, save note, search)",
                input_schema=MEMORY_TOOL_SCHEMA,
                handler=self.tool
            )
        ]
