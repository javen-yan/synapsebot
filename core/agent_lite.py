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



class AgentLite:
    def __init__(self):
        self.config = None
        self.registry = ToolRegistry()
        self.mcp_manager = MCPManager()
        self.llm_client = None
        self.agent: Optional[Agent] = None
        
    async def initialize(self):
        """Initializes the AgentLite application, loading config, tools, and creating the agent."""
        logger.print("[bold blue]AgentLite[/bold blue] Initializing...")
        
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
        skills = load_skills(skills_paths)
        logger.print(f"[green]Local Skills loaded[/green]: {len(skills)}")
        
        # 4. List All Available Tools
        tools = self.registry.list_tools()
        tools = self.registry.list_tools()
        logger.print(f"[green]Total Tools Registered[/green]: {len(tools)}")
        for t in tools:
            logger.print(f"  - [cyan]{t.name}[/cyan]: {t.description[:60]}...")

        # 5. Initialize Agent
        logger.print("\n[bold]Configuration Complete.[/bold] initializing Agent...")
        
        cwd = os.getcwd()
        system_ctx = f"You are AgentLite, a helpful AI assistant with access to the following tools.\n"
        system_ctx += f"Your current working directory is: {cwd}\n"
        system_ctx += "When using file or git tools, assume this directory unless specified otherwise.\n\n"
        # In future: system_ctx += format_skills_for_prompt(skills)
        
        self.llm_client = LLMClient(self.config.llm)
        self.llm_client = LLMClient(self.config.llm)
        self.agent = Agent(self.llm_client, self.registry, system_ctx)

    async def run(self, user_input: str):
        """Runs the agent with the given user input."""
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        await self.agent.run(user_input)
