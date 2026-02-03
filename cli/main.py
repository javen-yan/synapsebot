import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML

from core.logger import logger
from core.eventbus import BotRequest, BotResponse

async def start_cli():
    """Starts the interactive CLI session."""
    from core.synapse_bot import SynapseBot
    agent_app = SynapseBot()
    await agent_app.initialize()
    await agent_app.start()
    
    # Response handler for CLI
    response_queue = asyncio.Queue()
    
    async def handle_response(response: BotResponse):
        """Callback for handling responses from the event bus."""
        await response_queue.put(response)
    
    # Subscribe to CLI responses
    agent_app.event_bus.subscribe("response:cli", handle_response)
    
    # Interactive Loop
    logger.print("\n[bold blue]Ready! Type 'exit' to quit.[/bold blue]")
    
    session = PromptSession()
    chat_id = "cli-session"  # Single session for CLI
    
    from prompt_toolkit.patch_stdout import patch_stdout
    
    # Output Task
    async def output_loop():
        while True:
            response = await response_queue.get()
            msg_type = response.meta.get("type", "response")
            
            if msg_type == "response":
                # Display response
                logger.print(f"[bold cyan]Assistant:[/bold cyan] {response.content}")
            
            elif msg_type == "status":
                stage = response.meta.get("stage", "")
                if stage == "process":
                     # In a real concurrent CLI, updating the same line is hard if user is typing.
                     # We might skip status updates or log them as debug info, or print them above prompt.
                     # For now, let's just log them nicely via patch_stdout if they are important.
                     # Or skip to avoid clutter.
                     pass
            
            response_queue.task_done()

    # Create output task
    output_task = asyncio.create_task(output_loop())
    
    try:
        with patch_stdout():
            while True:
                user_input = await session.prompt_async(HTML("<b><ansigreen>User</ansigreen></b>: "))
                
                if user_input.lower() in ("exit", "quit"):
                    break
                
                if not user_input.strip():
                    continue
                
                # Publish request to event bus
                request = BotRequest(
                    source="cli",
                    chat_id=chat_id,
                    content=user_input,
                    stream=False
                )
                await agent_app.event_bus.publish("agent:request", request)
                # Note: We don't await response here anymore. It comes via output_loop.
                
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
    except Exception as e:
        logger.error(f"[red]Error:[/red] {e}")
    finally:
        output_task.cancel()
        await agent_app.stop()
