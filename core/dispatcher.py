import asyncio
from typing import Dict, Optional
from core.stage import AgentStage
from core.eventbus import EventBus, BotRequest, BotResponse
from core.agent import Agent
from core.config import Config
from core.tools import ToolRegistry
from core.llm import LLMClient
from core.logger import logger

class AgentDispatcher:
    def __init__(self, config: Config, registry: ToolRegistry, event_bus: EventBus, skills: list):
        self.config = config
        self.registry = registry
        self.event_bus = event_bus
        self.skills = skills
        self.llm_client = LLMClient(config.llm)
        self.sessions: Dict[str, Agent] = {} # Key: "{source}:{chat_id}"

        # Subscribe to requests
        self.event_bus.subscribe("agent:request", self.handle_request)

    async def handle_request(self, request: BotRequest):
        try:
            session_key = f"{request.source}:{request.chat_id}"
            agent = self.get_or_create_agent(session_key, request)
            
            # Send processing status (optional, if we want to support it via event bus)
            # await self.event_bus.publish(f"response:{request.source}", BotResponse(
            #     request_id=request.id,
            #     target=request.source,
            #     chat_id=request.chat_id,
            #     content="Thinking..."
            # ))

            async def stage_callback(stage: "AgentStage", status: str):
                 # Merge request meta with status meta
                 response_meta = {**request.meta, "type": "status_update", "stage": stage.value}
                 await self.event_bus.publish(f"response:{request.source}", BotResponse(
                    request_id=request.id,
                    target=request.source,
                    chat_id=request.chat_id,
                    content=status,
                    meta=response_meta
                ))

            # Run Agent
            # Note: The original agent.run takes a stage_callback. 
            # We need to adapt it.
            
            # Construct input text (append file info if needed)
            input_text = request.content
            if request.files:
                input_text += "\n[System: Attached files:]\n"
                for f in request.files:
                    # Depending on how we structured files in BotRequest. 
                    # If it's just meta, maybe we don't need to add to text if Agent supports it natively?
                    # Current Agent is text-based.
                    name = f.get("name", "unknown")
                    path = f.get("path", "")
                    input_text += f"- {name} ({path})\n"

            if request.stream:
                # Streaming Mode
                full_content = ""
                async for chunk in agent.run_raw_stream(input_text, stage_callback=stage_callback):
                    full_content += chunk
                    # Publish Chunk
                    chunk_meta = {**request.meta, "type": "chunk", "delta": True}
                    await self.event_bus.publish(f"response:{request.source}", BotResponse(
                        request_id=request.id,
                        target=request.source,
                        chat_id=request.chat_id,
                        content=chunk,
                        meta=chunk_meta
                    ))
                
                # Publish Final "Done" or just rely on chunks.
                # Ideally we want a final "complete" message like original but with full content?
                # Or just mark stream end.
                # Let's send a final message type "response" with full content for logs/history, 
                # but clients might ignore it if they consumed chunks.
                # Actually, clients might need to know when it's done. 
                # Existing `response` type serves that purpose.
                # Final response with merged meta
                final_meta = {**request.meta, "type": "response", "done": True}
                response = BotResponse(
                    request_id=request.id,
                    target=request.source,
                    chat_id=request.chat_id,
                    content=full_content,
                    meta=final_meta
                )
                await self.event_bus.publish(f"response:{request.source}", response)

            else:
                # Standard Mode
                response_content = await agent.run(input_text, stage_callback=stage_callback)
                
                # Publish Response with request meta
                response = BotResponse(
                    request_id=request.id,
                    target=request.source,
                    chat_id=request.chat_id,
                    content=response_content,
                    meta=request.meta  # Preserve request meta (e.g., message_id for Feishu)
                )
                await self.event_bus.publish(f"response:{request.source}", response)

        except Exception as e:
            logger.error(f"[Dispatcher] Error handling request {request.id}: {e}")
            # Error response with request meta
            error_response = BotResponse(
                request_id=request.id,
                target=request.source,
                chat_id=request.chat_id,
                content=f"Error processing request: {str(e)}",
                meta=request.meta  # Preserve request meta for error responses too
            )
            await self.event_bus.publish(f"response:{request.source}", error_response)

    def get_or_create_agent(self, session_key: str, request: BotRequest) -> Agent:
        if session_key not in self.sessions:
            system_prompt = self._get_system_prompt(request)
            self.sessions[session_key] = Agent(self.llm_client, self.registry, system_prompt)
            logger.info(f"[Dispatcher] Created new session: {session_key}")
        return self.sessions[session_key]

    def _get_system_prompt(self, request: BotRequest) -> str:
        # We can customize prompt based on source if needed
        import os
        cwd = os.getcwd()
        system_ctx = f"You are SynapseBot, a helpful AI assistant connected via {request.source}.\n"
        system_ctx += f"Current chat ID: {request.chat_id}\n"
        system_ctx += f"Your current working directory is: {cwd}\n"
        system_ctx += "Capabilities:\n"
        system_ctx += "- You can receive files and images sent by the user.\n"
        system_ctx += "- To send a file to the user, you MUST include a line in your response in this format: `[FILE: /absolute/path/to/file]`.\n"
        system_ctx += "  For example: `Here is the file you requested:\n[FILE: /root/data/report.pdf]`\n\n"
        
        from core.skills import format_skills_for_prompt
        system_ctx += format_skills_for_prompt(self.skills) + "\n\n"
        
        return system_ctx
