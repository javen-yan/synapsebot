import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.plugins.browser.plugin import BrowserPlugin

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def browser_plugin(mock_context):
    return BrowserPlugin(mock_context)

@pytest.mark.asyncio
async def test_web_search(browser_plugin):
    # Mock DuckDuckGo
    with patch("core.plugins.browser.tools.DDGS") as MockDDGS:
        mock_ddgs_instance = MockDDGS.return_value
        mock_ddgs_instance.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_instance.text.return_value = [
            {"title": "Test Result", "href": "http://example.com", "body": "Snippet"}
        ]
        
        result = await browser_plugin.browser_tools.web_search({"query": "test"})
        assert "Test Result" in result

@pytest.mark.asyncio
async def test_open_and_snapshot(browser_plugin):
    # Mock Playwright
    with patch("core.plugins.browser.tools.async_playwright") as mock_ap_func:
        # async_playwright() returns a ContextManager
        mock_context_manager = MagicMock()
        mock_ap_func.return_value = mock_context_manager
        
        # .start() is an AsyncMock method on the manager
        mock_playwright = AsyncMock()
        mock_context_manager.start = AsyncMock(return_value=mock_playwright)
        
        mock_browser = AsyncMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        
        # Mock evaluate return for snapshot
        mock_page.evaluate.return_value = "Title: Test Page\n[1] BUTTON - Submit"
        
        # Initialize
        await browser_plugin.initialize()
        
        # Test Open
        await browser_plugin.browser_tools.open_url({"url": "http://test.com"})
        mock_page.goto.assert_called_with("http://test.com", timeout=30000, wait_until="domcontentloaded")
        
        # Test Snapshot
        snap = await browser_plugin.browser_tools.snapshot({})
        assert "[1] BUTTON - Submit" in snap

@pytest.mark.asyncio
async def test_interaction(browser_plugin):
    with patch("core.plugins.browser.tools.async_playwright") as mock_ap_func:
        # Setup mocking structure same as above to pass initialization
        mock_context_manager = MagicMock()
        mock_ap_func.return_value = mock_context_manager
        mock_playwright = AsyncMock()
        mock_context_manager.start = AsyncMock(return_value=mock_playwright)
        
        mock_browser = AsyncMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_page = AsyncMock()
        # Setup page in tools
        browser_plugin.browser_tools.page = mock_page

        # Mock Locator
        mock_loc = AsyncMock()
        mock_loc.count.return_value = 1
        
        # page.locator is synchronous in Playwright, so we use MagicMock
        mock_page.locator = MagicMock(return_value=mock_loc)

        # Call click (will trigger initialize)
        await browser_plugin.browser_tools.click({"id": 1})
        
        # Verify
        mock_page.locator.assert_called_with('[data-agent-id="1"]')
        mock_loc.click.assert_called()
        
        # Type
        await browser_plugin.browser_tools.type_text({"id": 2, "text": "hello", "submit": True})
        mock_loc.fill.assert_called_with("hello", timeout=5000)
        mock_loc.press.assert_called_with("Enter")
