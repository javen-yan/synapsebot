from typing import List, Any
from core.plugins.base import Plugin
from core.tools import Tool
from core.plugins.browser.tools import (
    BrowserTools, 
    WEB_SEARCH_SCHEMA, OPEN_URL_SCHEMA, SNAPSHOT_SCHEMA, 
    CLICK_SCHEMA, TYPE_SCHEMA, SCROLL_SCHEMA, KEY_SCHEMA, 
    BACK_SCHEMA, SCREENSHOT_SCHEMA
)

class BrowserPlugin(Plugin):
    """
    Browser Plugin (Headless)
    
    Provides capabilities to search, browse, see, and interact with the web.
    """
    
    def __init__(self, context: Any = None):
        super().__init__(context)
        self.browser_tools = BrowserTools()

    async def initialize(self):
        """Initialize browser (lazy load handled in tools)."""
        pass

    async def close(self):
        if self.browser_tools:
            await self.browser_tools.close()

    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="web_search",
                description="Search the web using DuckDuckGo.",
                input_schema=WEB_SEARCH_SCHEMA,
                handler=self.browser_tools.web_search
            ),
            Tool(
                name="browser_open",
                description="Open a URL in the browser and see the page content.",
                input_schema=OPEN_URL_SCHEMA,
                handler=self.browser_tools.open_url
            ),
            Tool(
                name="browser_snapshot",
                description="Get a text snapshot of the current page with interactive Element IDs.",
                input_schema=SNAPSHOT_SCHEMA,
                handler=self.browser_tools.snapshot
            ),
            Tool(
                name="browser_click",
                description="Click an element by its ID (from snapshot).",
                input_schema=CLICK_SCHEMA,
                handler=self.browser_tools.click
            ),
            Tool(
                name="browser_type",
                description="Type text into an element by its ID (from snapshot).",
                input_schema=TYPE_SCHEMA,
                handler=self.browser_tools.type_text
            ),
            Tool(
                name="browser_scroll",
                description="Scroll the page up or down.",
                input_schema=SCROLL_SCHEMA,
                handler=self.browser_tools.scroll
            ),
             Tool(
                name="browser_press",
                description="Press a keyboard key (e.g. Enter, PageDown).",
                input_schema=KEY_SCHEMA,
                handler=self.browser_tools.press_key
            ),
            Tool(
                name="browser_back",
                description="Go back to the previous page.",
                input_schema=BACK_SCHEMA,
                handler=self.browser_tools.go_back
            ),
            Tool(
                name="browser_screenshot",
                description="Save a screenshot of the current page.",
                input_schema=SCREENSHOT_SCHEMA,
                handler=self.browser_tools.screenshot
            )
        ]

    async def context_prompt(self, request: Any = None) -> str:
        return ""
