"""
Browser management utilities for Zanichelli exercise automation.

This module handles browser setup, configuration, and lifecycle management.
"""

from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserManager:
    """Manages browser lifecycle and configuration."""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def setup_browser(
        self, 
        headless: bool = False,
        viewport: Dict[str, int] = None,
        user_agent: str = None,
        timeout: int = 10000
    ) -> Page:
        """
        Initialize browser and create a new page context.
        
        Args:
            headless: Whether to run browser in headless mode
            viewport: Browser viewport dimensions
            user_agent: Custom user agent string
            timeout: Default timeout for page operations
            
        Returns:
            The created page instance
        """
        print("Setting up browser...")
        
        # Default configurations
        if viewport is None:
            viewport = {'width': 1920, 'height': 1080}
        
        if user_agent is None:
            user_agent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/120.0.0.0 Safari/537.36')
        
        # Start Playwright
        self.playwright = await async_playwright().start()
        
        # Launch browser with reasonable settings
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Create context with specified settings
        self.context = await self.browser.new_context(
            viewport=viewport,
            user_agent=user_agent
        )
        
        # Create page
        self.page = await self.context.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(timeout)
        
        print(f"✓ Browser setup complete (headless: {headless})")
        return self.page
    
    async def navigate_to_url(
        self, 
        url: str, 
        wait_until: str = 'networkidle',
        timeout: int = 30000
    ) -> None:
        """
        Navigate to a URL and wait for it to load.
        
        Args:
            url: URL to navigate to
            wait_until: Wait condition ('load', 'domcontentloaded', 'networkidle')
            timeout: Navigation timeout in milliseconds
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        
        print(f"Navigating to: {url}")
        
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            print("✓ Page loaded successfully")
            
            # Wait a bit more for any dynamic content to load
            await self.page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"Warning: Navigation issue ({e}), but continuing...")
    
    async def take_screenshot(
        self, 
        path: str, 
        full_page: bool = True,
        quality: int = 90
    ) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            path: File path to save the screenshot
            full_page: Whether to capture the full page
            quality: JPEG quality (0-100)
            
        Returns:
            Path to the saved screenshot
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        
        try:
            # Wait for page to be fully loaded
            await self.page.wait_for_load_state('networkidle', timeout=5000)
            await self.page.wait_for_timeout(500)
            
            # Take screenshot
            await self.page.screenshot(
                path=path, 
                full_page=full_page,
                quality=quality if path.endswith('.jpg') or path.endswith('.jpeg') else None
            )
            
            print(f"✓ Screenshot saved: {path}")
            return path
            
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            # Fallback: basic screenshot
            try:
                await self.page.screenshot(path=path)
                print(f"✓ Basic screenshot saved: {path}")
                return path
            except Exception as final_error:
                print(f"Failed to take any screenshot: {final_error}")
                raise
    
    async def get_current_url(self) -> str:
        """Get the current page URL."""
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        return self.page.url
    
    async def go_back(self) -> None:
        """Navigate back to the previous page."""
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        
        try:
            await self.page.go_back()
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            print("✓ Navigated back to previous page")
        except Exception as e:
            print(f"Error navigating back: {e}")
    
    async def reload_page(self) -> None:
        """Reload the current page."""
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        
        try:
            await self.page.reload()
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            print("✓ Page reloaded")
        except Exception as e:
            print(f"Error reloading page: {e}")
    
    async def wait_for_timeout(self, timeout: int) -> None:
        """Wait for a specified amount of time."""
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        await self.page.wait_for_timeout(timeout)
    
    async def evaluate_javascript(self, script: str) -> Any:
        """
        Execute JavaScript in the browser context.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Result of the JavaScript execution
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        
        try:
            result = await self.page.evaluate(script)
            return result
        except Exception as e:
            print(f"Error executing JavaScript: {e}")
            return None
    
    async def get_page_title(self) -> str:
        """Get the current page title."""
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        return await self.page.title()
    
    async def cleanup(self) -> None:
        """Close browser and cleanup resources."""
        try:
            if self.browser:
                await self.browser.close()
                print("✓ Browser closed")
            
            if self.playwright:
                await self.playwright.stop()
                print("✓ Playwright stopped")
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None
    
    def is_initialized(self) -> bool:
        """Check if the browser is initialized and ready."""
        return self.page is not None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()