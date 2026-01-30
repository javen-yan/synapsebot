
import asyncio
import logging
import json
import os
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from core.config import Config
from core.agent import Agent
from core.llm import LLMClient
from core.tools import ToolRegistry
from core.logger import logger

class FeishuBot:
    def __init__(self, config: Config, registry: ToolRegistry):
        self.config = config
        self.registry = registry
        self.app_id = config.channels.feishu.app_id
        self.app_secret = config.channels.feishu.app_secret
        
        # Initialize internal clients
        self.llm_client = LLMClient(config.llm)
        self.sessions = {} # chat_id -> Agent

        # Build Event Handler
        self.event_handler = lark.EventDispatcherHandler.builder(
            "", 
            ""
        ).register_p2_im_message_receive_v1(self.handle_message_v1).build()

        # Build API Client
        self.client = lark.Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .log_level(lark.LogLevel.INFO) \
            .build()
            
        # Build WS Client
        self.ws_client = lark.ws.Client(
            self.app_id,
            self.app_secret,
            event_handler=self.event_handler,
            log_level=lark.LogLevel.INFO
        )

    async def start(self):
        """Starts the Feishu bot in WebSocket Mode."""
        logger.info("[bold green]Starting Feishu Bot (WebSocket)...[/bold green]")
        
        def run_ws():
            # Create a new loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Monkey-patch the loop in lark_oapi.ws.client
            # This is necessary because lark_oapi captures the loop at import time
            # and tries to use it in start().
            try:
                import lark_oapi.ws.client
                lark_oapi.ws.client.loop = loop
            except ImportError:
                logger.warning("Could not monkey-patch lark_oapi loop. This might cause issues.")

            self.ws_client.start()

        try:
            # lark-oapi's ws_client.start() is blocking.
            # We must run it in a separate thread to avoid blocking the asyncio loop.
            await asyncio.to_thread(run_ws)
        except Exception as e:
            logger.error(f"[red]Failed to start Feishu Bot:[/red] {e}")

    def get_or_create_agent(self, chat_id: str) -> Agent:
        if chat_id not in self.sessions:
            system_prompt = f"You are SynapseBot, a helpful AI assistant connected via Feishu.\n"
            system_prompt += f"Current chat ID: {chat_id}\n"
            
            self.sessions[chat_id] = Agent(self.llm_client, self.registry, system_prompt)
            logger.info(f"Created new session for Feishu chat: {chat_id}")
            
        return self.sessions[chat_id]

    def handle_message_v1(self, data: P2ImMessageReceiveV1) -> None:
        """Callback for lark-oapi to handle incoming messages."""
        # This function runs in the thread managed by lark-oapi (or the thread we started it in).
        # Since our Agent is async, we need to run the agent logic in an event loop.
        # However, lark's callback is synchronous.
        
        try:
            message = data.event.message
            chat_id = message.chat_id
            msg_type = message.message_type
            
            if msg_type != "text":
                logger.warning(f"[Feishu] Received unsupported message type: {msg_type}")
                return

            content = json.loads(message.content)
            text = content.get("text", "")
            
            # Remove @mentions if possible (simple approach)
            # mentions = message.mentions
            # if mentions:
            #     for mention in mentions:
            #         text = text.replace(mention.key, "").strip()
            
            logger.info(f"[Feishu] Msg from {chat_id}: {text}")
            
            # Run Agent Logic
            # We offload the agent processing to a task on the current loop (ws loop)
            # and use asyncio.to_thread for the blocking send_reply inside that task.
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.handle_message_async(chat_id, message.message_id, text))
            except RuntimeError:
                # Fallback if no loop is running
                 asyncio.run(self.handle_message_async(chat_id, message.message_id, text))
            
        except Exception as e:
            logger.error(f"[Feishu] Error handling message: {e}")

    async def process_agent_response(self, chat_id: str, user_input: str) -> str:
        agent = self.get_or_create_agent(chat_id)
        response = await agent.run(user_input)
        return response

    async def handle_message_async(self, chat_id: str, message_id: str, text: str):
        try:
            response_text = await self.process_agent_response(chat_id, text)
            # send_reply is blocking (requests), so run in thread
            await asyncio.to_thread(self.send_reply, message_id, response_text)
        except Exception as e:
            logger.error(f"[Feishu] Error in async message handler: {e}")

    def send_reply(self, message_id: str, text: str):
        content = json.dumps({"text": text})
        
        request = ReplyMessageRequest.builder() \
            .message_id(message_id) \
            .request_body(
                ReplyMessageRequestBody.builder()
                .content(content)
                .msg_type("text")
                .build()
            ) \
            .build()
            
        response = self.client.im.v1.message.reply(request)
        
        if not response.success():
            logger.error(f"[Feishu] Failed to reply: {response.code} - {response.msg}")
        else:
            logger.info(f"[Feishu] Reply sent to {message_id}")
