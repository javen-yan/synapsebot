import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Optional
from core.logger import logger

class MemoryManager:
    """Manages user memory files across different channels."""
    
    def __init__(self, memory_dir: Path):
        """
        Initialize MemoryManager.
        
        Args:
            memory_dir: Base directory for storing memory files
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"MemoryManager initialized with directory: {self.memory_dir}")
    
    def _get_memory_path(self, channel: str, user_id: str) -> Path:
        """Get the path to a user's memory file."""
        channel_dir = self.memory_dir / channel
        channel_dir.mkdir(parents=True, exist_ok=True)
        return channel_dir / f"{user_id}.md"
    
    async def get_memory(self, channel: str, user_id: str) -> str:
        """
        Load user's memory from file (async).
        
        Args:
            channel: Channel name (cli, web, feishu, slack)
            user_id: User identifier
            
        Returns:
            Memory content as string, or empty string if no memory exists
        """
        memory_path = self._get_memory_path(channel, user_id)
        
        if not memory_path.exists():
            logger.debug(f"No memory file found for {channel}:{user_id}")
            return ""
        
        try:
            async with aiofiles.open(memory_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            logger.debug(f"Loaded memory for {channel}:{user_id} ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"Error loading memory for {channel}:{user_id}: {e}")
            return ""
    
    async def save_interaction(self, channel: str, user_id: str, user_msg: str, agent_response: str):
        """
        Save a conversation interaction to user's memory file (async).
        
        Args:
            channel: Channel name
            user_id: User identifier
            user_msg: User's message
            agent_response: Agent's response
        """
        memory_path = self._get_memory_path(channel, user_id)
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create new memory file if it doesn't exist
        if not memory_path.exists():
            await self._create_memory_file(memory_path, channel, user_id, now)
        
        # Append the interaction
        try:
            async with aiofiles.open(memory_path, 'a', encoding='utf-8') as f:
                await f.write(f"\n### {date_str}\n")
                await f.write(f"- **User**: {user_msg[:200]}{'...' if len(user_msg) > 200 else ''}\n")
                # Summarize response if too long
                response_summary = agent_response[:300] + '...' if len(agent_response) > 300 else agent_response
                await f.write(f"- **Assistant**: {response_summary}\n")
            
            logger.debug(f"Saved interaction to memory: {channel}:{user_id}")
        except Exception as e:
            logger.error(f"Error saving interaction to memory: {e}")
    
    async def _create_memory_file(self, path: Path, channel: str, user_id: str, timestamp: datetime):
        """Create a new memory file with header (async)."""
        created_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        header = f"""# User Memory: {user_id}

**Channel**: {channel}  
**Created**: {created_str}  
**Last Updated**: {created_str}

## Recent Conversations
"""
        
        try:
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(header)
            logger.info(f"Created new memory file: {path}")
        except Exception as e:
            logger.error(f"Error creating memory file: {e}")
    
    async def get_memory_summary(self, channel: str, user_id: str, max_length: int = 2000) -> str:
        """
        Get a summarized version of user's memory for context (async).
        
        Args:
            channel: Channel name
            user_id: User identifier
            max_length: Maximum length of summary
            
        Returns:
            Summarized memory content
        """
        memory = await self.get_memory(channel, user_id)
        
        if not memory:
            return ""
        
        # If memory is short enough, return as is
        if len(memory) <= max_length:
            return memory
        
        # Otherwise, take the header and most recent conversations
        # Run processing in thread as it's CPU bound (string split/join)
        def _process(mem_content):
            lines = mem_content.split('\n')
            header_lines = []
            conversation_lines = []
            in_conversations = False
            
            for line in lines:
                if line.startswith('## Recent Conversations'):
                    in_conversations = True
                    conversation_lines.append(line)
                elif in_conversations:
                    conversation_lines.append(line)
                else:
                    header_lines.append(line)
            
            # Take header and last N conversation entries
            header = '\n'.join(header_lines)
            recent = '\n'.join(conversation_lines[-50:])  # Last ~50 lines of conversations
            
            summary = f"{header}\n{recent}"
            
            # If still too long, truncate
            if len(summary) > max_length:
                summary = summary[-max_length:]
                summary = "...\n" + summary[summary.find('\n')+1:]  # Start from next line
            return summary

        return await asyncio.to_thread(_process, memory)
