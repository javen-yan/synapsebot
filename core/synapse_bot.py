import logging
import os
import asyncio
from typing import Optional
from core.logger import logger
from core.config import get_config
from core.skills import load_skills
from core.tools import ToolRegistry
from core.mcp_client import MCPManager
from core.eventbus import EventBus
from core.dispatcher import AgentDispatcher

class SynapseBot:
    """
    SynapseBot: The main application container.
    Manages EventBus, Dispatcher, and Integrations.
    """
    def __init__(self):
        self.config = None
        self.registry = ToolRegistry()
        self.mcp_manager = MCPManager()
        self.llm_client = None
        self.skills = []
        self.event_bus = EventBus()
        self.dispatcher: Optional[AgentDispatcher] = None
        self.web_bot: Optional['WebBot'] = None
        
    async def initialize(self):
        """Initializes the SynapseBot application."""
        logger.print("[bold blue]SynapseBot[/bold blue] Initializing...")
        
        # 1. Load Config
        try:
            self.config = get_config()
            logger.configure(level=self.config.log_level)
            logger.print(f"[green]Config loaded[/green]: {self.config.llm.model}")
            
            level_str = self.config.log_level.upper()
            if level_str != "DEBUG":
                logging.getLogger("mcp").setLevel(logging.WARNING)
                logging.getLogger("httpx").setLevel(logging.WARNING)
                logging.getLogger("httpcore").setLevel(logging.WARNING)
        except Exception as e:
            logger.error(f"[red]Error loading config:[/red] {e}")
            raise

        # 2. Load MCP Servers
        logger.warning("[yellow]Connecting to MCP Servers...[/yellow]")
        await self.mcp_manager.load_mcp_servers(
            [self.config.storage.system_mcp_config_path, self.config.storage.user_mcp_config_path],
            self.registry
        )
        await asyncio.sleep(5) 
        
        # 3. Load Local Skills
        skills_paths = [self.config.storage.system_skills_path, self.config.storage.user_skills_path]
        self.skills = load_skills(skills_paths)
        logger.print(f"[green]Local Skills loaded[/green]: {len(self.skills)}")
        
        # 4. Initialize Dispatcher
        self.dispatcher = AgentDispatcher(self.config, self.registry, self.event_bus, self.skills)

    async def start(self):
        """Starts background services (Dispatcher, etc)."""
        if self.dispatcher:
            await self.dispatcher.start()
        
        # 5. List Tools
        tools = self.registry.list_tools()
        logger.print(f"[green]Total Tools Registered[/green]: {len(tools)}")
        logger.print("[bold green]SynapseBot Services Started[/bold green]")

    async def stop(self):
        """Stops the application and cleans up resources."""
        logger.print("[bold yellow]SynapseBot Stopping...[/bold yellow]")
        if self.dispatcher:
            await self.dispatcher.stop()
            
        await self.mcp_manager.stop_all_servers()
        
        # Close LLM Client if it has close method (depends on implementation)
        # if self.llm_client: ...
        
        logger.print("[bold green]Goodbye![/bold green]")

    async def reload_skills(self):
        """Reloads skills from disk."""
        skills_paths = [self.config.storage.system_skills_path, self.config.storage.user_skills_path]
        self.skills = load_skills(skills_paths)
        # Also update dispatcher
        if self.dispatcher:
            self.dispatcher.skills = self.skills
        logger.info(f"Skills reloaded: {len(self.skills)}")

    async def reload_mcp(self):
        """Reloads MCP servers from config."""
        logger.warning("[yellow]Reloading MCP Servers...[/yellow]")
        await self.mcp_manager.stop_all_servers()
        self.registry.clear()
        
        from core.config import get_config
        self.config = get_config(reload=True)
        
        await self.mcp_manager.load_mcp_servers(
            [self.config.storage.system_mcp_config_path, self.config.storage.user_mcp_config_path],
            self.registry
        )
        logger.print(f"[green]MCP Servers Reloaded[/green]. Tools count: {len(self.registry.list_tools())}")
