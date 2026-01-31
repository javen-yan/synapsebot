from typing import Dict, Any, List, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import uuid
import time
from core.logger import logger

class BotRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str  # e.g., "feishu", "slack", "web"
    chat_id: str
    content: str
    stream: bool = False
    files: List[Dict[str, Any]] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

class BotResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: Optional[str] = None
    target: str  # e.g., "feishu", "slack", "web"
    chat_id: str
    content: str
    files: List[str] = Field(default_factory=list) # List of file paths
    meta: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    
class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Awaitable[None]]]] = {}

    def subscribe(self, topic: str, handler: Callable[[Any], Awaitable[None]]):
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)
        logger.debug(f"[EventBus] Subscribed to {topic} with {handler.__name__}")

    async def publish(self, topic: str, event: Any):
        logger.debug(f"[EventBus] Publishing to {topic}: {event}")
        if topic in self._subscribers:
            for handler in self._subscribers[topic]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"[EventBus] Error in handler {handler.__name__} for topic {topic}: {e}")
