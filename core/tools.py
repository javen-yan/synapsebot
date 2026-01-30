from typing import Any, Dict, List, Optional, Callable, Awaitable
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ToolResult(BaseModel):
    content: str
    is_error: bool = False

class Tool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Awaitable[Any]]

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, name: str, description: str, handler: Callable, input_schema: Dict[str, Any]):
        self._tools[name] = Tool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler
        )

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())
    
    def to_openai_tools(self) -> List[Dict[str, Any]]:
        """Converts tools to OpenAI format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in self._tools.values()
        ]
