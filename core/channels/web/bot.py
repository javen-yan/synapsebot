from core.stage import AgentStage
import asyncio
import os
import uuid
import json
from typing import Dict, List, Optional, Callable, Awaitable
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.channels.base import BaseChannel
from core.config import Config
from core.tools import ToolRegistry
from core.eventbus import EventBus, BotRequest, BotResponse
from core.logger import logger

class WebBot(BaseChannel):
    @property
    def workspace_name(self) -> str:
        return "web"

    def __init__(self, config: Config, registry: ToolRegistry, event_bus: EventBus):
        super().__init__(config, registry, event_bus)
        # Store active connections: chat_id -> callback
        self.connections: Dict[str, Callable[[str], Awaitable[None]]] = {}
        
        self.router = APIRouter()
        self.router.websocket("/ws/chat")(self.websocket_chat)

    async def start(self):
        logger.info("[Web] Starting WebBot...")

    async def websocket_chat(self, websocket: WebSocket):
        await websocket.accept()
        
        # Generate new chat_id per connection
        chat_id = str(uuid.uuid4())
        logger.info(f"[Web-WS] New connection: {chat_id}")
        
        async def send_callback(message: str):
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"[Web-WS] Error sending to {chat_id}: {e}")

        try:
            # Register connection
            await self.register_connection(chat_id, send_callback)
            
            # Send welcome message
            await websocket.send_text(json.dumps({"type": "status", "content": "Connected to SynapseBot"}))
            
            while True:
                data = await websocket.receive_text()
                try:
                    payload = json.loads(data)
                    text = payload.get("text", "")
                    files = payload.get("files", []) 
                except json.JSONDecodeError:
                    text = data
                    files = []
                
                if text or files:
                    await self.handle_message(chat_id, text, files)
                
        except WebSocketDisconnect:
            logger.info(f"[Web-WS] Disconnected: {chat_id}")
        except Exception as e:
            logger.error(f"[Web-WS] Error in connection {chat_id}: {e}")
        finally:
            await self.unregister_connection(chat_id)

    async def register_connection(self, chat_id: str, send_callback: Callable[[str], Awaitable[None]]):
        """Registers a new WebSocket connection."""
        self.connections[chat_id] = send_callback
        logger.info(f"[Web] Connection registered for {chat_id}")

    async def unregister_connection(self, chat_id: str):
        """Unregisters a WebSocket connection."""
        if chat_id in self.connections:
            del self.connections[chat_id]
            logger.info(f"[Web] Connection unregistered for {chat_id}")

    async def handle_message(self, chat_id: str, text: str, files: List = None):
        """
        Handles an incoming message from WebSocket.
        Publishes a BotRequest to the EventBus.
        
        Args:
            chat_id: Chat session ID
            text: Message text
            files: List of file objects with structure:
                   [{"name": "file.pdf", "url": "/files/xxx", "size": 1024, "type": "application/pdf"}]
        """
        # Prepare file meta
        files_meta = []
        if files:
            for file_obj in files:
                # If it's a dict with url, extract the actual file path
                if isinstance(file_obj, dict):
                    url = file_obj.get("url", "")
                    # Extract filename from URL: /files/xxx.pdf -> xxx.pdf
                    filename = url.split("/")[-1] if url else ""
                    # Construct full path
                    file_path = os.path.join(self.config.storage.upload_dir, filename) if filename else ""
                    
                    files_meta.append({
                        "path": file_path,
                        "name": file_obj.get("name", filename),
                        "size": file_obj.get("size", 0),
                        "type": file_obj.get("type", "application/octet-stream")
                    })
                elif isinstance(file_obj, str):
                    # Legacy: direct path string
                    files_meta.append({
                        "path": file_obj,
                        "name": os.path.basename(file_obj)
                    })

        request = BotRequest(
            source=self.workspace_name,
            chat_id=chat_id,
            content=text,
            stream=True, # Enable streaming
            files=files_meta
        )

        await self.publish_request(request)

    async def send(self, response: BotResponse):
        """
        Receives response from EventBus and sends it via the registered callback.
        """
        chat_id = response.chat_id
        callback = self.connections.get(chat_id)
        
        if not callback:
            logger.warning(f"[Web] No active connection for {chat_id}. Dropping response.")
            return

        try:
            # Check for status update or final response
            msg_type = response.meta.get("type", "response")
            content = response.content

            if msg_type == "status_update":
                stage = response.meta.get("stage", "process")
                payload = json.dumps({"type": "status", "content": content, "stage": stage})
            elif msg_type == "chunk":
                # Stream chunk
                payload = json.dumps({"type": "chunk", "content": content, "stage": AgentStage.RESPONSE.value})
            else:
                # Final response (type="response")
                # Check for file attachments in response
                import re
                file_pattern = re.compile(r"\[FILE:\s*(.*?)\]")
                file_paths = file_pattern.findall(content)
                
                # Convert file paths to file objects with URLs
                files_info = []
                if file_paths:
                    for file_path in file_paths:
                        file_path = file_path.strip()
                        if os.path.exists(file_path):
                            filename = os.path.basename(file_path)
                            file_size = os.path.getsize(file_path)
                            
                            # Determine MIME type
                            import mimetypes
                            mime_type, _ = mimetypes.guess_type(file_path)
                            
                            files_info.append({
                                "name": filename,
                                "url": f"/files/{filename}",
                                "size": file_size,
                                "type": mime_type or "application/octet-stream"
                            })
                
                # Remove [FILE: ...] markers from content
                clean_content = file_pattern.sub("", content).strip()
                
                # Send final message if there are file attachments
                if files_info:
                    payload = json.dumps({
                        "type": "message", 
                        "content": clean_content,
                        "files": files_info
                    })
                    await callback(payload)
                
                # Always send done signal to indicate streaming is complete
                done_payload = json.dumps({"type": "done"})
                await callback(done_payload)
                return

            await callback(payload)
            
        except Exception as e:
            logger.error(f"[Web] Error sending to connection {chat_id}: {e}")
