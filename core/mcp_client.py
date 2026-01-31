import asyncio
import os
import json
import shutil
import logging
from typing import Dict, List, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.tools import ToolRegistry
from core.logger import logger

class MCPManager:
    def __init__(self):
        self.sessions: List[ClientSession] = []
        self.tasks: List[asyncio.Task] = []
        self._exit_stack = None

    async def load_mcp_servers(self, config_paths: List[str], registry: ToolRegistry):
        combined_servers = {}

        for config_path in config_paths:
            if not os.path.exists(config_path):
                logger.warning(f"MCP config not found: {config_path}")
                continue

            with open(config_path, "r") as f:
                try:
                    config = json.load(f)
                    servers = config.get("mcpServers", {})
                    
                    # Resolve relative paths in args/command based on config file location
                    config_dir = os.path.dirname(os.path.abspath(config_path))
                    
                    for name, server_config in servers.items():
                        # Resolve command
                        cmd = server_config.get("command", "")
                        if cmd.startswith("./") or cmd.startswith(".\\"):
                            server_config["command"] = os.path.join(config_dir, cmd)
                            
                        # Resolve args
                        args = server_config.get("args", [])
                        new_args = []
                        for arg in args:
                            if isinstance(arg, str) and (arg.startswith("./") or arg.startswith(".\\")):
                                new_args.append(os.path.join(config_dir, arg))
                            else:
                                new_args.append(arg)
                        server_config["args"] = new_args
                        
                    combined_servers.update(servers)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in {config_path}")
                    continue

        for name, server_config in combined_servers.items():
            command = server_config.get("command")
            args = server_config.get("args", [])
            env = server_config.get("env", {})
            
            # Merge with current env
            full_env = os.environ.copy()
            full_env.update(env)
            
            # Pass LOG_LEVEL to subprocess if set in logging
            if logging.getLogger().level > logging.INFO:
                 full_env["LOG_LEVEL"] = "WARNING"
                 full_env["MCP_LOG_LEVEL"] = "WARNING"
            elif logging.getLogger().level == logging.INFO:
                 full_env["LOG_LEVEL"] = "INFO"
                 full_env["MCP_LOG_LEVEL"] = "INFO"
            
            # Resolve command path if needed (e.g. npx/uvx)
            import sys
            if command in ["python", "python3"]:
                executable = sys.executable
            else:
                executable = shutil.which(command)
                if not executable:
                    # Fallback to command name if not found in path
                     executable = command

            if logging.getLogger().level <= logging.INFO:
                logger.info(f"Connecting to MCP server: {name} ({executable} {' '.join(args)})")

            server_params = StdioServerParameters(
                command=executable,
                args=args,
                env=full_env
            )

            task = asyncio.create_task(self._run_server(name, server_params, registry))
            self.tasks.append(task)

    async def _run_server(self, name: str, params: StdioServerParameters, registry: ToolRegistry):
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.sessions.append(session)

                    # List Tools
                    result = await session.list_tools()
                    
                    for tool in result.tools:
                        tool_name = tool.name
                        
                        async def make_handler(s: ClientSession, t_name: str):
                            async def handler(args: Dict[str, Any]):
                                return await s.call_tool(t_name, arguments=args)
                            return handler

                        registry.register(
                            name=tool_name,
                            description=tool.description or "",
                            input_schema=tool.inputSchema,
                            handler=await make_handler(session, tool_name),
                            source=name
                        )
                        if logging.getLogger().level <= logging.INFO:
                            logger.info(f"  Registered MCP tool: {tool_name} (from {name})")

                    # Keep the connection alive
                    await asyncio.get_running_loop().create_future()
                    
        except asyncio.CancelledError:
            logger.info(f"MCP Server {name} task cancelled")
        except Exception as e:
            import traceback
            logger.error(f"Error in MCP Server {name}: {e}")
            traceback.print_exc()

    async def stop_all_servers(self):
        """Stops all running MCP servers."""
        for task in self.tasks:
            task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        self.tasks = []
        self.sessions = []
        logger.info("Stopped all MCP servers")

