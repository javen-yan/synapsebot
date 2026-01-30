import asyncio
import sys
import os
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML

from rich.console import Console
from core.logger import logger

console = Console()

async def async_main():
    from core.agent_lite import AgentLite
    agent_app = AgentLite()
    await agent_app.initialize()
    
    
    # 7. Interactive Loop
    logger.print("\n[bold blue]Ready! Type 'exit' to quit.[/bold blue]")
    
    session = PromptSession()
    
    while True:
        try:
            user_input = await session.prompt_async(HTML("<b><ansigreen>User</ansigreen></b>: "))
            
            if user_input.lower() in ("exit", "quit"):
                break
            
            if not user_input.strip():
                continue
                
            await agent_app.run(user_input)
            
        except KeyboardInterrupt:
            break
        except EOFError:
            break
        except Exception as e:
            logger.error(f"[red]Error:[/red] {e}")

    # Terminate
    logger.print("[bold]Goodbye![/bold]")

if __name__ == "__main__":
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass
