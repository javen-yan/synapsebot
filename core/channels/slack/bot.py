import os
import re
import aiohttp
from typing import List
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from core.config import Config
from core.tools import ToolRegistry
from core.logger import logger
from core.eventbus import EventBus, BotRequest, BotResponse
from core.channels.base import BaseChannel

class SlackBot(BaseChannel):
    @property
    def workspace_name(self) -> str:
        return "slack"

    def __init__(self, config: Config, registry: ToolRegistry, event_bus: EventBus):
        super().__init__(config, registry, event_bus)
        self.app = AsyncApp(token=config.channels.slack.bot_token)
        self.handler = AsyncSocketModeHandler(self.app, config.channels.slack.app_token)
        self.bot_token = config.channels.slack.bot_token
        
        # Register event handlers
        self.app.message()(self.handle_message)
        self.app.event("app_mention")(self.handle_app_mention)

    async def start(self):
        """Starts the Slack bot in Socket Mode."""
        logger.info("[bold blue]Starting Slack Bot...[/bold blue]")
        try:
            await self.handler.start_async()
        except Exception as e:
            logger.error(f"[red]Failed to start Slack Bot:[/red] {e}")

    async def handle_message(self, message, say):
        """Handles incoming messages (DMs or channels where bot is present)."""
        # Ignore bot's own messages
        if message.get("bot_id"):
            return
            
        # In public channels, only respond to mentions (handled by app_mention) or if it's a DM
        channel_type = message.get("channel_type")
        if channel_type == "channel": # Public channel
            pass 
        elif channel_type == "im": # Direct Message
            await self.process_message(message, say)

    async def handle_app_mention(self, event, say):
        """Handles @mentions in channels."""
        await self.process_message(event, say)

    async def process_message(self, event, say):
        channel_id = event["channel"]
        user_id = event["user"]
        user_input = event.get("text", "")
        ts = event.get("ts")
        
        # Clean up mention text if present e.g. <@U123456>
        user_input = re.sub(r"<@U[A-Z0-9]+>", "", user_input).strip()
        
        # Handle attachments/files
        files = event.get("files")
        files_meta = []
        if files:
            logger.info(f"[Slack] Processing {len(files)} files from message")
            saved_paths = await self.download_and_save_files(files)
            for path in saved_paths:
                files_meta.append({
                    "path": path,
                    "name": os.path.basename(path)
                })
        
        if not user_input and not files:
            return

        logger.debug(f"[Slack] Msg from {channel_id}: {user_input}")
        
        # Create Request
        request = BotRequest(
            source=self.workspace_name,
            chat_id=channel_id,
            content=user_input,
            files=files_meta,
            meta={"ts": ts, "user": user_id} # Store timestamp to reply in thread if needed
        )
        
        await self.publish_request(request)

    async def send(self, response: BotResponse):
        """Handle response from Dispatcher."""
        channel_id = response.chat_id
        content = response.content
        ts = response.meta.get("ts") # We might not get it back unless we persisted it in session or echo it.
        # But dispatcher might not echo generic meta. 
        # Actually EventBus doesn't guarantee preserving meta roundtrip unless we enforce it.
        # Assuming Dispatcher echoes NOTHING from request meta by default unless specific.
        # However, for Threading, we need ts. Even if simple reply, we just post to channel.
        
        try:
             # Check for status update
            msg_type = response.meta.get("type", "response")
            
            if msg_type == "status":
                # Maybe post ephemeral? Or update a "thinking" message?
                # Hard to track "thinking" message ID without state.
                # Just ignore for now or log
                logger.debug(f"[Slack] Status: {content}")
                return

            # Clean content (remove [FILE:...] tags intended for other bots?)
            # Agent output usually has [FILE: ...] if it generates files.
            
            # Find files to upload
            files_to_upload = []
            import re
            file_pattern = re.compile(r"\[FILE:\s*(.*?)\]")
            file_matches = file_pattern.findall(content)
            for path in file_matches:
                clean_path = path.strip()
                if os.path.exists(clean_path) and os.path.isfile(clean_path):
                    files_to_upload.append(clean_path)
            
            clean_content = file_pattern.sub("", content).strip()
            
            # Send text
            if clean_content:
                await self.app.client.chat_postMessage(
                    channel=channel_id,
                    text=clean_content,
                    thread_ts=ts # if we had it. If not, just channel.
                )
            
            # Upload files
            for file_path in files_to_upload:
                try:
                    logger.info(f"[Slack] Uploading file: {file_path}")
                    await self.app.client.files_upload_v2(
                        channel=channel_id,
                        file=file_path,
                        filename=os.path.basename(file_path),
                        # thread_ts=ts 
                    )
                except Exception as e:
                    logger.error(f"[Slack] Failed to upload file {file_path}: {e}")

        except Exception as e:
            logger.error(f"[Slack] Error sending response: {e}")

    async def download_and_save_files(self, files: List[dict]) -> List[str]:
        """Downloads files from Slack, handling the auth redirect dance."""
        saved_paths = []
        token = self.config.channels.slack.bot_token
        
        async with aiohttp.ClientSession() as session:
            for file_info in files:
                url = file_info.get("url_private_download") or file_info.get("url_private")
                filename = file_info.get("name")
                if not url or not filename:
                    continue
                
                try:
                    # Initial request with Auth header check for redirect
                    headers = {"Authorization": f"Bearer {token}"}
                    async with session.get(url, headers=headers, allow_redirects=False) as resp:
                        if 300 <= resp.status < 400:
                            redirect_url = resp.headers.get("Location")
                            if redirect_url:
                                # Follow redirect without Auth header (pre-signed URL)
                                async with session.get(redirect_url) as resp2:
                                    content = await resp2.read()
                            else:
                                content = await resp.read()
                        else:
                            content = await resp.read()

                    # Save file
                    filepath = os.path.join(self.download_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(content)
                    
                    saved_paths.append(filepath)
                    logger.info(f"[Slack] Downloaded file: {filepath}")
                    
                except Exception as e:
                    logger.error(f"[Slack] Failed to download file {filename}: {e}")
        
        return saved_paths

