from abc import ABC, abstractmethod
from typing import Dict, Any
from core.config import Config
from core.tools import ToolRegistry
from core.logger import logger
from core.eventbus import EventBus, BotRequest, BotResponse

class BaseChannel(ABC):
    def __init__(self, config: Config, registry: ToolRegistry, event_bus: EventBus):
        self.config = config
        self.registry = registry
        self.event_bus = event_bus
        self.download_dir = self._init_workspace()
        
        # Subscribe to responses targeted at this channel
        self.event_bus.subscribe(f"response:{self.workspace_name}", self.handle_response)

    @property
    @abstractmethod
    def workspace_name(self) -> str:
        """Name of the channel workspace (e.g. 'slack', 'feishu')."""
        pass

    def _init_workspace(self) -> str:
        """Initialize the workspace directory for the channel."""
        import os
        path = os.path.join(self.config.storage.data_path, "downloads", self.workspace_name)
        os.makedirs(path, exist_ok=True)
        return path
        
    @abstractmethod
    async def start(self):
        """Start the channel client (e.g. connect to WebSocket)."""
        pass

    async def publish_request(self, request: BotRequest):
        """Publish a request to the EventBus."""
        await self.event_bus.publish("agent:request", request)

    async def handle_response(self, response: BotResponse):
        """Handle a response from the EventBus."""
        if response.target != self.workspace_name:
            return
        
        logger.debug(f"[{self.workspace_name}] Received response for {response.chat_id}")
        await self.send(response)

    @abstractmethod
    async def send(self, response: BotResponse):
        """Send the response to the user via the channel."""
        pass
