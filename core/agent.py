import json
import asyncio
from typing import List, Dict, Any, Callable, Awaitable, Optional
from rich.markdown import Markdown
from mcp.types import TextContent, ImageContent, EmbeddedResource
from core.llm import LLMClient
from core.tools import ToolRegistry
from core.logger import logger

from core.stage import AgentStage

class Agent:
    def __init__(self, llm: LLMClient, registry: ToolRegistry, system_prompt: str):
        self.llm = llm
        self.registry = registry
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

    async def run(self, user_input: str, stage_callback: Optional[Callable[[AgentStage, str], Awaitable[None]]] = None):
        self.messages.append({"role": "user", "content": user_input})
        
        # Notify PROMPT stage
        if stage_callback:
            await stage_callback(AgentStage.PROMPT, user_input)
        
        while True:
            # 1. Think
            logger.debug("[dim]Thinking...[/dim]")
            if stage_callback:
                await stage_callback(AgentStage.PROCESS, "Thinking...")

            tools_schema = self.registry.to_openai_tools()
            
            try:
                response = await self.llm.chat(self.messages, tools=tools_schema)
                message = response.choices[0].message
            except Exception as e:
                logger.error(f"LLM Error: {e}")
                return "I encountered an error while thinking."

            self.messages.append(message)

            # 2. Act (if tool calls)
            if message.tool_calls:
                logger.debug(f"[bold blue]Tool Calls:[/bold blue] {len(message.tool_calls)}")
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments_str = tool_call.function.arguments
                    call_id = tool_call.id
                    
                    
                    logger.debug(f"  -> Calling [cyan]{function_name}[/cyan] with {arguments_str}")
                    if stage_callback:
                        await stage_callback(AgentStage.PROCESS, f"Calling tool: {function_name}")         
                    
                    try:
                        arguments = json.loads(arguments_str)
                        tool = self.registry.get_tool(function_name)
                        
                        if tool:
                            # Execute Tool
                            # Check if handler is async
                            if asyncio.iscoroutinefunction(tool.handler):
                                result = await tool.handler(arguments)
                            else:
                                result = tool.handler(arguments)
                            
                            if isinstance(result, (list, tuple)):
                                 # Parse list of content
                                final_text = []
                                for item in result:
                                    if isinstance(item, TextContent):
                                        final_text.append(item.text)
                                    elif isinstance(item, ImageContent):
                                        final_text.append(f"[Image content: {item.mimeType}]")
                                    elif isinstance(item, EmbeddedResource):
                                        final_text.append(f"[Embedded resource: {item.resource.uri}]")
                                    else:
                                        final_text.append(str(item))
                                output = "\n".join(final_text)
                            elif hasattr(result, 'content') and isinstance(result.content, list):
                                 # Parse MCP Result object
                                final_text = []
                                for item in result.content:
                                    if isinstance(item, TextContent):
                                        final_text.append(item.text)
                                    elif isinstance(item, ImageContent):
                                        final_text.append(f"[Image content: {item.mimeType}]")
                                    elif isinstance(item, EmbeddedResource):
                                        final_text.append(f"[Embedded resource: {item.resource.uri}]")
                                    else:
                                        final_text.append(str(item))
                                output = "\n".join(final_text)
                            else:
                                output = str(result)
                            
                            # Truncate for display but keep full for context
                            display_output = output[:500] + "..." if len(output) > 500 else output
                            # Truncate for display but keep full for context
                            display_output = output[:500] + "..." if len(output) > 500 else output
                            logger.debug(f"  <- Result: [dim]{display_output}[/dim]")
    
                        else:
                            output = f"Error: Tool {function_name} not found."
                            logger.error(f"  <- Result: {output}")

                    except json.JSONDecodeError:
                        output = "Error: Invalid JSON arguments."
                        logger.error(f"  <- Result: {output}")
                    except Exception as e:
                        output = f"Error executing tool: {str(e)}"
                        logger.error(f"  <- Result: {output}")
                
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": output
                })
            else:
                # Top level response (Final Answer)
                content = message.content
                logger.print(f"\n[bold green]Agent:[/bold green]")
                logger.print(Markdown(content))
                return content

    async def run_raw_stream(self, user_input: str, stage_callback: Optional[Callable[[AgentStage, str], Awaitable[None]]] = None):
        """Runs the agent and yields raw text chunks."""
        self.messages.append({"role": "user", "content": user_input})
        
        # Notify PROMPT stage
        if stage_callback:
            await stage_callback(AgentStage.PROMPT, user_input)
        
        while True:
            # 1. Think
            logger.debug("[dim]Thinking...[/dim]")
            if stage_callback:
                await stage_callback(AgentStage.PROCESS, "Thinking...")
                
            tools_schema = self.registry.to_openai_tools()
            
            try:
                response = await self.llm.chat(self.messages, tools=tools_schema)
                message = response.choices[0].message
            except Exception as e:
                logger.error(f"LLM Error in stream: {e}")
                msg = f"Error: {str(e)}"
                # Yield error as content
                yield msg
                return

            self.messages.append(message)

            # If tool calls, execute them silently (no streaming for tools yet)
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments_str = tool_call.function.arguments
                    call_id = tool_call.id
                    
                    if stage_callback:
                        await stage_callback(AgentStage.PROCESS, f"Calling tool: {function_name}")
                        
                    try:
                        arguments = json.loads(arguments_str)
                        tool = self.registry.get_tool(function_name)
                        
                        if tool:
                            # Execute Tool
                            if asyncio.iscoroutinefunction(tool.handler):
                                result = await tool.handler(arguments)
                            else:
                                result = tool.handler(arguments)
                            
                            # Parse result
                            if isinstance(result, (list, tuple)):
                                final_text = []
                                for item in result:
                                    if isinstance(item, TextContent):
                                        final_text.append(item.text)
                                    elif isinstance(item, ImageContent):
                                        final_text.append(f"[Image content: {item.mimeType}]")
                                    elif isinstance(item, EmbeddedResource):
                                        final_text.append(f"[Embedded resource: {item.resource.uri}]")
                                    else:
                                        final_text.append(str(item))
                                output = "\n".join(final_text)
                            elif hasattr(result, 'content') and isinstance(result.content, list):
                                final_text = []
                                for item in result.content:
                                    if isinstance(item, TextContent):
                                        final_text.append(item.text)
                                    elif isinstance(item, ImageContent):
                                        final_text.append(f"[Image content: {item.mimeType}]")
                                    else:
                                        final_text.append(str(item))
                                output = "\n".join(final_text)
                            else:
                                output = str(result)
                        else:
                            output = f"Error: Tool {function_name} not found."
                        
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": output
                        })
                    except Exception as e:
                        error_msg = f"Error calling {function_name}: {str(e)}"
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": error_msg
                        })
            else:
                # Top-level response. 
                # Simulate streaming by chunking the final content.
                content = message.content or ""
                
                # In a real streaming LLM client, we would yield chunks from llm.chat_stream
                # Here we just chunk the static response.
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    # Add newline except for last line
                    chunk = line + ('\n' if i < len(lines) - 1 else '')
                    yield chunk
                    await asyncio.sleep(0.02) # Small delay to simulate stream
                return