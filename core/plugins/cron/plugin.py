from typing import List, Any
from core.plugins.base import Plugin
from core.tools import Tool
from core.plugins.cron.tool import CronTool, CRON_TOOL_SCHEMA
from core.plugins.cron.service import CronService
from core.plugins.cron.store import CronStore

class CronPlugin(Plugin):
    def __init__(self, context: Any = None):
        super().__init__(context)
        self.service = None
        self.tool = None

    async def initialize(self):
        # Context is expected to be the AgentDispatcher or Config object
        # We need storage config and event bus
        config = self.context.config
        event_bus = self.context.event_bus
        
        store = CronStore(config.storage)
        self.service = CronService(store, event_bus)
        await self.service.start()
        
        self.tool = CronTool(self.service)

    def get_tools(self) -> List[Tool]:
        if not self.tool:
            return []
            
        return [
            Tool(
                name="cron",
                description=self.tool.__doc__ or "Manage cron jobs",
                input_schema=CRON_TOOL_SCHEMA,
                handler=self.tool
            )
        ]
