import logging
import asyncio
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from ddgs import DDGS

logger = logging.getLogger(__name__)

# --- Schemas ---

OPEN_URL_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {"type": "string", "description": "The URL to visit."}
    },
    "required": ["url"]
}

SNAPSHOT_SCHEMA = {
    "type": "object",
    "properties": {},
    "description": "Examine the current page content and get IDs for interactive elements."
}

CLICK_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "The numeric ID of the element to click (from snapshot)."}
    },
    "required": ["id"]
}

TYPE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "description": "The numeric ID of the field to type into."},
        "text": {"type": "string", "description": "The text to type."},
        "submit": {"type": "boolean", "description": "Whether to press Enter after typing.", "default": False}
    },
    "required": ["id", "text"]
}

SCROLL_SCHEMA = {
    "type": "object",
    "properties": {
        "direction": {"type": "string", "enum": ["up", "down"], "default": "down"},
        "amount": {"type": "integer", "description": "Amount to scroll in pixels (default: 500).", "default": 500}
    },
    "required": []
}

KEY_SCHEMA = {
    "type": "object",
    "properties": {
        "key": {"type": "string", "description": "Key to press (e.g., Enter, Escape, PageDown)."}
    },
    "required": ["key"]
}

BACK_SCHEMA = {
    "type": "object",
    "properties": {},
    "description": "Go back to the previous page."
}

SCREENSHOT_SCHEMA = {
    "type": "object",
    "properties": {},
    "description": "Take a screenshot of the current page."
}

WEB_SEARCH_SCHEMA = {
     "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The search query to find information about."
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return (default: 5, max: 10).",
            "default": 5
        }
    },
    "required": ["query"]
}

# --- Browser Tools Implementation ---

class BrowserTools:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        if self.playwright:
            return
        self.playwright = await async_playwright().start()
        # Launch Chromium (headless by default)
        try:
             self.browser = await self.playwright.chromium.launch(headless=True)
             self.context = await self.browser.new_context(
                 user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                 viewport={"width": 1280, "height": 800}
             )
             self.page = await self.context.new_page()
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise e

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    async def _ensure_page(self):
        if not self.page:
            await self.initialize()

    # --- Tool Handlers ---

    async def web_search(self, args: Dict[str, Any]) -> str:
        """Same as before: DuckDuckGo search."""
        query = args.get("query")
        max_results = min(args.get("max_results", 5), 10)
        
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(r)
            
            if not results:
                return "No results found."

            formatted = f"## Search Results for '{query}'\n\n"
            for i, res in enumerate(results, 1):
                title = res.get("title", "No Title")
                href = res.get("href", "#")
                body = res.get("body", "No snippet")
                formatted += f"{i}. [{title}]({href})\n   {body}\n\n"
                
            return formatted
        except Exception as e:
            return f"Search error: {e}"

    async def open_url(self, args: Dict[str, Any]) -> str:
        url = args.get("url")
        await self._ensure_page()
        try:
            await self.page.goto(url, timeout=30000, wait_until="domcontentloaded")
            return await self.snapshot({})
        except Exception as e:
            return f"Error opening URL: {e}"

    async def snapshot(self, args: Dict[str, Any]) -> str:
        """Injects IDs and returns a text snapshot."""
        await self._ensure_page()
        try:
            # Inject generic tagging script
            # This script finds interactive elements, assigns a unique data-agent-id if missing,
            # and returns a text structure.
            # We use a simple counter 1..N reset on every snapshot for simplicity? 
            # Or persistent? Let's do persistent for the session but reset if page navigates.
            # Ideally reset on every snapshot so numbers are small (1-50) and easy to type.
            
            js_script = """
            () => {
                let idCounter = 1;
                const elements = [];
                
                // Remove existing tags
                document.querySelectorAll('[data-agent-id]').forEach(el => el.removeAttribute('data-agent-id'));

                // Query interesting elements
                const selectors = [
                    'a[href]', 'button', 'input', 'textarea', 'select', 
                    '[role="button"]', '[role="link"]', '[role="menuitem"]',
                    '[tabindex]:not([tabindex="-1"])'
                ];
                
                const candidates = document.querySelectorAll(selectors.join(','));
                
                let textResult = `Title: ${document.title}\\nURL: ${document.location.href}\\n\\n`;
                
                candidates.forEach(el => {
                    // Filter invisible
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return;
                    
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) return;

                    // Assign ID
                    const id = idCounter++;
                    el.setAttribute('data-agent-id', id.toString());
                    
                    // Generate description
                    let name = el.innerText.slice(0, 50).replace(/\\n/g, ' ').trim();
                    if (!name) name = el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.getAttribute('name') || el.tagName.toLowerCase();
                    
                    textResult += `[${id}] ${el.tagName} - ${name}`;
                    if(el.tagName === 'INPUT') textResult += ` (value: ${el.value})`;
                    textResult += '\\n';
                });

                if (idCounter === 1) textResult += "No interactive elements found.";
                return textResult;
            }
            """
            result = await self.page.evaluate(js_script)
            return result
        except Exception as e:
             return f"Snapshot error: {e}"

    async def click(self, args: Dict[str, Any]) -> str:
        uid = str(args.get("id"))
        await self._ensure_page()
        try:
            loc = self.page.locator(f'[data-agent-id="{uid}"]')
            if await loc.count() == 0:
                return f"Error: Element [{uid}] not found. Take a new snapshot."
            
            await loc.click(timeout=5000)
            return f"Clicked element [{uid}]."
        except Exception as e:
            return f"Click error: {e}"

    async def type_text(self, args: Dict[str, Any]) -> str:
        uid = str(args.get("id"))
        text = args.get("text")
        submit = args.get("submit", False)
        
        await self._ensure_page()
        try:
            loc = self.page.locator(f'[data-agent-id="{uid}"]')
            if await loc.count() == 0:
                return f"Error: Element [{uid}] not found."
            
            await loc.fill(text, timeout=5000)
            msg = f"Typed '{text}' into [{uid}]."
            
            if submit:
                await loc.press("Enter")
                msg += " Pressed Enter."
            
            return msg
        except Exception as e:
            return f"Type error: {e}"

    async def scroll(self, args: Dict[str, Any]) -> str:
        direction = args.get("direction", "down")
        amount = args.get("amount", 500)
        await self._ensure_page()
        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            else:
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            return f"Scrolled {direction} by {amount}px."
        except Exception as e:
            return f"Scroll error: {e}"
    
    async def press_key(self, args: Dict[str, Any]) -> str:
        key = args.get("key")
        await self._ensure_page()
        try:
            await self.page.keyboard.press(key)
            return f"Pressed key: {key}"
        except Exception as e:
            return f"Key error: {e}"

    async def go_back(self, args: Dict[str, Any]) -> str:
        await self._ensure_page()
        try:
            await self.page.go_back()
            return "Navigated back."
        except Exception as e:
            return f"Back error: {e}"
    
    async def screenshot(self, args: Dict[str, Any]) -> str:
        await self._ensure_page()
        try:
            import base64
            # We can't return the binary image directly to the agent text creation usually, 
            # unless we save it as an artifact.
            # For now, let's save to a temp file and return path?
            # Or just confirm it was taken if we can't display it.
            # The agent tool protocol might support "image" type but here we return string.
            # Let's save to a standard path in workspace.
            
            path = "browser_screenshot.png"
            await self.page.screenshot(path=path)
            return f"Screenshot saved to {path} (in current working directory)."
        except Exception as e:
            return f"Screenshot error: {e}"
