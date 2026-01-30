from openai import AsyncOpenAI
from core.config import LLMConfig

class LLMClient:
    def __init__(self, config: LLMConfig):
        self.client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key
        )
        self.model = config.model

    async def chat(self, messages: list, tools: list = None):
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            
        return await self.client.chat.completions.create(**kwargs)
