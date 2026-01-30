import asyncio
import os
from core.config import load_config
from core.tools import ToolRegistry
from core.mcp_client import MCPManager
from core.llm import LLMClient
from core.agent import Agent

async def test_main():
    print("Testing AgentLite...")
    
    config = load_config()
    registry = ToolRegistry()
    mcp_manager = MCPManager()
    
    print("Loading MCP...")
    await mcp_manager.load_mcp_servers(
        [config.storage.system_mcp_config_path, config.storage.user_mcp_config_path],
        registry
    )
    await asyncio.sleep(5) # Wait for MCP
    
    cwd = os.getcwd()
    system_ctx = f"You are a helpful assistant. Your current working directory is {cwd}."
    llm_client = LLMClient(config.llm)
    agent = Agent(llm_client, registry, system_ctx)
    
    print("Running Agent with query: 'what is the git status?'")
    response = await agent.run("what is the git status?")
    print("Final Response:", response)

if __name__ == "__main__":
    asyncio.run(test_main())
