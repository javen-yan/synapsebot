from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML

from core.logger import logger

async def start_cli():
    """Starts the interactive CLI session."""
    from core.synapse_bot import SynapseBot
    agent_app = SynapseBot()
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
