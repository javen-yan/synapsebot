import logging
import os
import asyncio
from typing import List, Optional
from rich.console import Console
from core.logger import logger
from core.config import load_config
from core.skills import load_skills, format_skills_for_prompt
from core.tools import ToolRegistry
from core.mcp_client import MCPManager
from core.llm import LLMClient
from core.agent import Agent

class SynapseBot(Agent):
    """
    SynapseBot: A lightweight agent with Skills and MCP support.
    """
    def __init__(self):
        self.config = None
        self.registry = ToolRegistry()
        self.mcp_manager = MCPManager()
        self.llm_client = None
        self.agent: Optional[Agent] = None
        self.skills = []
        
    async def initialize(self):
        """Initializes the SynapseBot application, loading config, tools, and creating the agent."""
        logger.print("[bold blue]SynapseBot[/bold blue] Initializing...")
        
        # 1. Load Config
        try:
            self.config = load_config()
            
            # Configure logging based on config
            logger.configure(level=self.config.log_level)
            logger.print(f"[green]Config loaded[/green]: {self.config.llm.model}")
            
            level_str = self.config.log_level.upper()
            
            # Suppress noisy libraries unless DEBUG
            if level_str != "DEBUG":
                logging.getLogger("mcp").setLevel(logging.WARNING)
                logging.getLogger("httpx").setLevel(logging.WARNING)
            
        except Exception as e:
            logger.error(f"[red]Error loading config:[/red] {e}")
            raise

        # 2. Load MCP Servers
        logger.warning("[yellow]Connecting to MCP Servers...[/yellow]")
        await self.mcp_manager.load_mcp_servers(
            [self.config.storage.system_mcp_config_path, self.config.storage.user_mcp_config_path],
            self.registry
        )
        
        # Give a moment for MCP servers to connect and tools to register
        await asyncio.sleep(5) 
        
        # 3. Load Local Skills
        skills_paths = [self.config.storage.system_skills_path, self.config.storage.user_skills_path]
        self.skills = load_skills(skills_paths)
        logger.print(f"[green]Local Skills loaded[/green]: {len(self.skills)}")
        
        # 4. List All Available Tools
        tools = self.registry.list_tools()
        logger.print(f"[green]Total Tools Registered[/green]: {len(tools)}")
        for t in tools:
            logger.print(f"  - [cyan]{t.name}[/cyan]: {t.description[:60]}...")

        # 5. Initialize Agent
        logger.print("\n[bold]Configuration Complete.[/bold] initializing Agent...")
        
        cwd = os.getcwd()
        system_ctx = f"You are SynapseBot, a helpful AI assistant with access to the following tools.\n"
        system_ctx += f"Your current working directory is: {cwd}\n"
        system_ctx += "When using file or git tools, assume this directory unless specified otherwise.\n\n"
        
        # Add skills to system context
        from core.skills import format_skills_for_prompt
        system_ctx += format_skills_for_prompt(self.skills) + "\n\n"
        
        self.llm_client = LLMClient(self.config.llm)
        self.agent = Agent(self.llm_client, self.registry, system_ctx)

    async def run(self, user_input: str):
        """Runs the agent with the given user input."""
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        await self.agent.run(user_input)

    async def reload_skills(self):
        """Reloads skills from disk."""
        skills_paths = [self.config.storage.system_skills_path, self.config.storage.user_skills_path]
        self.skills = load_skills(skills_paths)
        logger.info(f"Skills reloaded: {len(self.skills)}")

    async def reload_mcp(self):
        """Reloads MCP servers from config."""
        logger.warning("[yellow]Reloading MCP Servers...[/yellow]")
        
        # 1. Stop existing servers
        await self.mcp_manager.stop_all_servers()
        
        # 2. Clear registry
        self.registry.clear()
        
        # 3. Reload from config
        # We need to re-load config in case it changed on disk
        self.config = load_config()
        
        await self.mcp_manager.load_mcp_servers(
            [self.config.storage.system_mcp_config_path, self.config.storage.user_mcp_config_path],
            self.registry
        )
        
        # 4. Update Agent (optional, but good practice if agent caches anything)
        # In this lite version, Agent just holds ref to registry, so it sees changes immediately
        
        logger.print(f"[green]MCP Servers Reloaded[/green]. Tools count: {len(self.registry.list_tools())}")

