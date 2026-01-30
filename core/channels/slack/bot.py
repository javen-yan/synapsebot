import os
import re
import aiohttp
from typing import List
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from core.config import Config
from core.agent import Agent
from core.llm import LLMClient
from core.tools import ToolRegistry
from core.logger import logger

class SlackBot:
    def __init__(self, config: Config, registry: ToolRegistry):
        self.config = config
        self.registry = registry
        self.app = AsyncApp(token=config.channels.slack.bot_token)
        self.handler = AsyncSocketModeHandler(self.app, config.channels.slack.app_token)
        self.llm_client = LLMClient(config.llm)

        self.download_dir = os.path.join(config.storage.data_path, "downloads", "slack")
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Session storage: channel_id -> Agent
        self.sessions = {}
        
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

    def get_or_create_agent(self, channel_id: str) -> Agent:
        if channel_id not in self.sessions:
            system_prompt = f"You are SynapseBot, a helpful AI assistant connected via Slack.\n"
            system_prompt += f"Current channel ID: {channel_id}\n"
            system_prompt += "Capabilities:\n"
            system_prompt += "- You can receive files sent by the user.\n"
            system_prompt += "- To send a file to the user, you MUST include a line in your response in this format: `[FILE: /absolute/path/to/file]`.\n"
            system_prompt += "  For example: `Here is the file you requested:\n[FILE: /root/data/report.pdf]`\n"
            
            self.sessions[channel_id] = Agent(self.llm_client, self.registry, system_prompt)
            logger.info(f"Created new session for channel: {channel_id}")
            
        return self.sessions[channel_id]

    async def handle_message(self, message, say):
        """Handles incoming messages (DMs or channels where bot is present)."""
        # Ignore bot's own messages
        if message.get("bot_id"):
            return
            
        # In public channels, only respond to mentions (handled by app_mention) or if it's a DM
        channel_type = message.get("channel_type")
        if channel_type == "channel": # Public channel
            # We mostly rely on app_mention for public channels to avoid noise
            pass 
        elif channel_type == "im": # Direct Message
            await self.process_message(message, say)

    async def handle_app_mention(self, event, say):
        """Handles @mentions in channels."""
        await self.process_message(event, say)

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
                    # Handle duplicate filenames? For now, overwrite or append timestamp could be better but let's keep simple
                    with open(filepath, "wb") as f:
                        f.write(content)
                    
                    saved_paths.append(filepath)
                    logger.info(f"[Slack] Downloaded file: {filepath}")
                    
                except Exception as e:
                    logger.error(f"[Slack] Failed to download file {filename}: {e}")
        
        return saved_paths

    async def process_message(self, event, say):
        channel_id = event["channel"]
        user_input = event.get("text", "")
        
        # Clean up mention text if present e.g. <@U123456>
        user_input = re.sub(r"<@U[A-Z0-9]+>", "", user_input).strip()
        
        # Handle attachments/files
        files = event.get("files")
        if files:
            logger.info(f"[Slack] Processing {len(files)} files from message")
            saved_paths = await self.download_and_save_files(files)
            if saved_paths:
                file_note = "\n[System: User attached files:]\n" + "\n".join([f"- {path}" for path in saved_paths])
                user_input += file_note
        
        if not user_input and not files:
            return

        logger.info(f"[Slack] Msg from {channel_id}: {user_input}")
        
        agent = self.get_or_create_agent(channel_id)
        
        try:
            response = await agent.run(user_input)
            
            # Check for file uploads in response
            files_to_upload = []
            
            # 1. Explicit [FILE: path] format (Preferred)
            file_pattern = re.compile(r"\[FILE:\s*(.*?)\]")
            file_matches = file_pattern.findall(response)
            for path in file_matches:
                clean_path = path.strip()
                if os.path.exists(clean_path) and os.path.isfile(clean_path):
                    files_to_upload.append(clean_path)
            
            # 2. Markdown link fallback: ![alt](path) or [text](path)
            link_pattern = re.compile(r"!?\[.*?\]\((.*?)\)")
            link_matches = link_pattern.findall(response)
            
            for path in link_matches:
                clean_path = path.replace("file://", "")
                # Avoid duplicates
                if clean_path not in files_to_upload and os.path.exists(clean_path) and os.path.isfile(clean_path):
                    files_to_upload.append(clean_path)
            
            # Clean response text by removing [FILE: ...] tags
            # We don't remove markdown links as they might be useful text even if we send the file, 
            # or maybe we should? For now, let's just remove the explicit command we taught the agent.
            clean_response = file_pattern.sub("", response).strip()
            
            # Send the text response FIRST (so it introduces the files)
            if clean_response:
                await say(clean_response)

            if files_to_upload:
                # Upload files
                for file_path in files_to_upload:
                    try:
                        logger.info(f"[Slack] Uploading file: {file_path}")
                        await self.app.client.files_upload_v2(
                            channel=channel_id,
                            file=file_path,
                            filename=os.path.basename(file_path),
                            # initial_comment=f"Sending {os.path.basename(file_path)}" # Optional now that we text first
                        )
                    except Exception as e:
                        logger.error(f"[Slack] Failed to upload file {file_path}: {e}")
                        await say(f"⚠️ Failed to upload {os.path.basename(file_path)}: {e}")
            
        except Exception as e:
            logger.error(f"[Slack] Error processing message: {e}")
            await say(f"⚠️ Error: {str(e)}")
