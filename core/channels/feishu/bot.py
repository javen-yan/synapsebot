import asyncio
import json
import os
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from typing import Callable, Awaitable, List
from core.config import Config
from core.tools import ToolRegistry
from core.logger import logger
from core.eventbus import EventBus, BotRequest, BotResponse

from core.channels.base import BaseChannel
from core.channels.feishu.converter import markdown_to_feishu_post

class FeishuBot(BaseChannel):
    @property
    def workspace_name(self) -> str:
        return "feishu"

    def __init__(self, config: Config, registry: ToolRegistry, event_bus: EventBus):
        super().__init__(config, registry, event_bus)
        self.app_id = config.channels.feishu.app_id
        self.app_secret = config.channels.feishu.app_secret

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
            try:
                import lark_oapi.ws.client
                lark_oapi.ws.client.loop = loop
            except ImportError:
                logger.warning("Could not monkey-patch lark_oapi loop. This might cause issues.")

            self.ws_client.start()

        try:
            # lark-oapi's ws_client.start() is blocking.
            await asyncio.to_thread(run_ws)
        except Exception as e:
            logger.error(f"[red]Failed to start Feishu Bot:[/red] {e}")

    def handle_message_v1(self, data: P2ImMessageReceiveV1) -> None:
        """Callback for lark-oapi to handle incoming messages."""
        try:
            message = data.event.message
            chat_id = message.chat_id
            msg_type = message.message_type
            message_id = message.message_id
            
            content = json.loads(message.content)
            text = ""
            files = []
            
            if msg_type == "text":
                text = content.get("text", "")
            elif msg_type == "image":
                image_key = content.get("image_key")
                files.append({"type": "image", "key": image_key})
                text = "[System: User sent an image]"
            elif msg_type == "file":
                file_key = content.get("file_key")
                file_name = content.get("file_name", "unknown_file")
                files.append({"type": "file", "key": file_key, "name": file_name})
                text = f"[System: User sent a file: {file_name}]"
            elif msg_type == "media": # Video etc
                file_key = content.get("file_key")
                file_name = content.get("file_name", "unknown_video")
                files.append({"type": "media", "key": file_key, "name": file_name})
                text = f"[System: User sent a video: {file_name}]"
            else:
                logger.warning(f"[Feishu] Received unsupported message type: {msg_type}")
                return

            logger.info(f"[Feishu] Msg from {chat_id}: {text}")
            
            # Run Async Logic
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.handle_message_async(chat_id, message_id, text, files))
            except RuntimeError:
                 asyncio.run(self.handle_message_async(chat_id, message_id, text, files))
            
        except Exception as e:
            logger.error(f"[Feishu] Error handling message: {e}")

    async def handle_message_async(self, chat_id: str, message_id: str, text: str, files: List[dict]):
        try:
            # Download files first and add paths to request
            # We can download them now or let Agent/Dispatcher handle it?
            # Better to download now so we have local paths.
            saved_paths = await self.download_files(message_id, files)
            
            # Convert saved_paths to file objects for Request
            request_files = []
            for path in saved_paths:
                request_files.append({
                    "path": path,
                    "name": os.path.basename(path)
                })

            # Create Request
            request = BotRequest(
                source=self.workspace_name,
                chat_id=chat_id,
                content=text,
                files=request_files,
                meta={"message_id": message_id} # Store message_id to reply later
            )
            
            # Publish Request
            await self.publish_request(request)

        except Exception as e:
            logger.error(f"[Feishu] Error in async message handler: {e}")

    async def send(self, response: BotResponse):
        """Handle response from Dispatcher."""
        try:
            message_id = response.meta.get("message_id")
            if not message_id:
                logger.warning(f"[Feishu] No message_id in response meta for {response.chat_id}")
                # Use chat_id to send a fresh message if message_id is missing?
                # But we don't know how to initiate chat without message_id in this logic mostly.
                # Actually we can send fresh message to chat_id.
                return

            # Check if this is a status update, chunk, or final response
            msg_type = response.meta.get("type", "response")
            
            if msg_type == "status_update":
                # We can't really "stream" updates exclusively to the same bubble easily without
                # keeping track of a "response bubble ID".
                # For simplicity, let's just log it or maybe send ephemeral "thinking" if we haven't.
                # Implementation choice: Just log distinct statuses for now to avoid spam.
                logger.debug(f"[Feishu] Status Update: {response.content}")
                return
            
            if msg_type == "chunk":
                # Feishu doesn't support streaming in the same way as Web
                # We'll accumulate chunks and send the final response
                logger.debug(f"[Feishu] Received chunk (ignoring for now)")
                return

            # Send Final Response (type="response")
            # send_reply is sync, run in thread
            await asyncio.to_thread(self.send_reply, message_id, response.content, response.chat_id)
            
        except Exception as e:
             logger.error(f"[Feishu] Error sending response: {e}")

    async def send_text_reply(self, message_id: str, text: str) -> str:
        """Sends a simple text reply and returns the message_id.""" 
        # (Same as before, utility)
        try:
            content = json.dumps({"text": text})
            req = ReplyMessageRequest.builder() \
                .message_id(message_id) \
                .request_body(ReplyMessageRequestBody.builder().content(content).msg_type("text").build()) \
                .build()
            
            resp = await asyncio.to_thread(self.client.im.v1.message.reply, req)
            if resp.success():
                return resp.data.message_id
            else:
                logger.error(f"[Feishu] Failed to send text reply: {resp.code} - {resp.msg}")
                return None
        except Exception as e:
            logger.error(f"[Feishu] Exception sending text reply: {e}")
            return None

    # Keeping download_files, send_reply, send_file mostly same but ensuring they are robust
    async def download_files(self, message_id: str, files: List[dict]) -> List[str]:
        # ... (reuse existing logic)
        saved_paths = []
        for f in files:
            key = f.get("key")
            name = f.get("name", f"{key}.{f.get('type')}")
            file_type = f.get("type")
            if not key: continue
            
            try:
                resource_type = "image" if file_type == "image" else "file"
                req = GetMessageResourceRequest.builder() \
                    .message_id(message_id) \
                    .file_key(key) \
                    .type(resource_type) \
                    .build()
                resp = await asyncio.to_thread(self.client.im.v1.message_resource.get, req)
                
                if not resp.success():
                    logger.error(f"[Feishu] Failed to download {file_type} {key}: {resp.code} - {resp.msg}")
                    continue
                
                file_content = resp.file.read()
                save_path = os.path.join(self.download_dir, name)
                with open(save_path, "wb") as f_out:
                    f_out.write(file_content)
                saved_paths.append(save_path)
                logger.info(f"[Feishu] Downloaded {file_type} to {save_path}")
            except Exception as e:
                logger.error(f"[Feishu] Exception downloading {key}: {e}")
        return saved_paths

    def send_reply(self, message_id: str, text: str, chat_id: str = None):
        """
        Sends a reply. If text contains [FILE: path], uploads and sends file.
        Also handles normal text reply.
        """
        # Parse for files
        import re
        file_pattern = re.compile(r"\[FILE:\s*(.*?)\]")
        file_matches = file_pattern.findall(text)
        
        files_to_send = []
        for path in file_matches:
            clean_path = path.strip()
            if os.path.exists(clean_path) and os.path.isfile(clean_path):
                files_to_send.append(clean_path)
        
        # Clean text
        clean_text = file_pattern.sub("", text).strip()
        
        # Send text first
        if clean_text:
            try:
                post_content = markdown_to_feishu_post(clean_text)
                rich_text_content = {
                    "zh_cn": {
                        "title": "", 
                        "content": post_content
                    }
                }
                content_str = json.dumps(rich_text_content)
                request = ReplyMessageRequest.builder() \
                    .message_id(message_id) \
                    .request_body(ReplyMessageRequestBody.builder().content(content_str).msg_type("post").build()) \
                    .build()
                self.client.im.v1.message.reply(request)
            except Exception as e:
                logger.error(f"[Feishu] Failed to send rich text reply: {e}")
                # Fallback
                text_content = json.dumps({"text": clean_text})
                request = ReplyMessageRequest.builder() \
                    .message_id(message_id) \
                    .request_body(ReplyMessageRequestBody.builder().content(text_content).msg_type("text").build()) \
                    .build()
                self.client.im.v1.message.reply(request)

        # Send files
        for file_path in files_to_send:
            self.send_file(chat_id, file_path)

    def send_file(self, chat_id: str, file_path: str):
        # ... (reuse existing logic)
        try:
            import mimetypes
            file_name = os.path.basename(file_path)
            file_type = "file"
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and mime_type.startswith("image"):
                file_type = "image"
                
            with open(file_path, "rb") as f:
                if file_type == "image":
                    req = CreateImageRequest.builder() \
                        .request_body(CreateImageRequestBody.builder().image_type("message").image(f).build()) \
                        .build()
                    resp = self.client.im.v1.image.create(req)
                    if resp.success():
                        image_key = resp.data.image_key
                        content = json.dumps({"image_key": image_key})
                        self.client.im.v1.message.create(
                            CreateMessageRequest.builder()
                            .receive_id_type("chat_id")
                            .request_body(CreateMessageRequestBody.builder().receive_id(chat_id).content(content).msg_type("image").build())
                            .build()
                        )
                else:
                    req = CreateFileRequest.builder() \
                        .request_body(CreateFileRequestBody.builder().file_type("stream").file_name(file_name).file(f).build()) \
                        .build()
                    resp = self.client.im.v1.file.create(req)
                    if resp.success():
                        file_key = resp.data.file_key
                        content = json.dumps({"file_key": file_key})
                        self.client.im.v1.message.create(
                            CreateMessageRequest.builder()
                            .receive_id_type("chat_id")
                            .request_body(CreateMessageRequestBody.builder().receive_id(chat_id).content(content).msg_type("file").build())
                            .build()
                        )
        except Exception as e:
            logger.error(f"[Feishu] Failed to send file {file_path}: {e}")
