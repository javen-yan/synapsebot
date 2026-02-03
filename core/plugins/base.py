from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.tools import Tool

class Plugin(ABC):
    """Abstract base class for SynapseBot plugins."""
    
    def __init__(self, context: Any = None):
        self.context = context

    @abstractmethod
    async def initialize(self):
        """Initialize the plugin (async)."""
        pass

    @property
    def name(self) -> str:
        """Plugin name."""
        return self.__class__.__name__.lower().replace("plugin", "")

    def get_tools(self) -> List[Tool]:
        """Return a list of tools provided by this plugin."""
        return []

    async def context_prompt(self, request: Any = None) -> str:
        """Return a system prompt snippet to inject into the agent's context."""
        return ""
