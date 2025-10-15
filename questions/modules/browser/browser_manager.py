"""
Browser management utilities for Zanichelli exercise automation.

This module handles browser setup, configuration, and lifecycle management.
"""

from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from pathlib import Path


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
        timeout: int = 10000,
        state_file: str = None
    ) -> Page:
        """
        Initialize browser and create a new page context.
        
        Args:
            headless: Whether to run browser in headless mode
            viewport: Browser viewport dimensions
            user_agent: Custom user agent string
            timeout: Default timeout for page operations
            state_file: Path to browser state file for session persistence
            
        Returns:
            The created page instance
        """
        print("Setting up browser...")
        
        # Default configurations
        #if viewport is None:
        #    viewport = {'width': 1920, 'height': 1080}
        
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
        context_options = {
            'viewport': viewport,
            'user_agent': user_agent
        }
        
        # Load saved state if available
        if state_file and Path(state_file).exists():
            print(f"Loading browser state from: {state_file}")
            context_options['storage_state'] = state_file
        
        self.context = await self.browser.new_context(**context_options)
        
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
    
    async def hide_footer(self) -> bool:
        """
        Hide the footer element on the page.
        
        Returns:
            True if footer was found and hidden, False otherwise
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        
        try:
            # Method 1: Use the specific DOM structure and add footer class
            footer_found = await self.page.evaluate('''
                () => {
                    // Navigate through the specific DOM structure
                    const root = document.querySelector('div#root');
                    if (!root) {
                        console.log('Root div not found');
                        return false;
                    }
                    
                    // Find div with display="inline-flex" inside root
                    const inlineFlexDiv = root.querySelector('div[display="inline-flex"]');
                    if (!inlineFlexDiv) {
                        console.log('Inline-flex div not found');
                        return false;
                    }
                    
                    // Get all first-level div children
                    const firstLevelDivs = Array.from(inlineFlexDiv.children).filter(child => child.tagName.toLowerCase() === 'div');
                    if (firstLevelDivs.length === 0) {
                        console.log('No first-level div children found');
                        return false;
                    }
                    
                    // Get the last div from first-level children
                    const lastDiv = firstLevelDivs[firstLevelDivs.length - 1];
                    
                    // Find div with display="flex" and width="100%" inside the last div
                    const footerDiv = lastDiv.querySelector('div[display="flex"][width="100%"]');
                    if (!footerDiv) {
                        console.log('Footer div with display="flex" width="100%" not found');
                        return false;
                    }
                    
                    // Add footer class and hide it
                    footerDiv.classList.add('footer');
                    footerDiv.setAttribute('data-hidden-by-automation', 'true');
                    
                    console.log('Footer found and marked with footer class');
                    return true;
                }
            ''')
            
            if footer_found:
                # Method 2: Add CSS rule to hide elements with footer class
                await self.page.add_style_tag(content='''
                    .footer {
                        visibility: hidden !important;
                    }
                ''')
                print("✓ Footer container found, marked with 'footer' class, and hidden using CSS rule")
                return True
            else:
                print("Footer container not found using DOM structure path")
                return False
            
        except Exception as e:
            print(f"Error hiding footer: {e}")
            return False
    
    async def show_footer(self) -> bool:
        """
        Show the footer element that was previously hidden.
        
        Returns:
            True if footer was found and shown, False otherwise
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        
        try:
            # Method 1: Remove the CSS rule that hides footer elements
            await self.page.add_style_tag(content='''
                .footer {
                    visibility: visible !important;
                }
            ''')
            
            # Method 2: Remove footer class from elements
            footer_restored = await self.page.evaluate('''
                () => {
                    const footerElements = document.querySelectorAll('.footer[data-hidden-by-automation="true"]');
                    let restored = false;
                    
                    footerElements.forEach(footer => {
                        footer.removeAttribute('data-hidden-by-automation');
                        footer.classList.remove('footer');
                        restored = true;
                        console.log('Footer class removed and visibility restored');
                    });
                    
                    return restored;
                }
            ''')
            
            if footer_restored:
                print("✓ Footer container visibility restored by removing CSS rule and footer class")
            else:
                print("No hidden footer container found to restore")
            
            return footer_restored
            
        except Exception as e:
            print(f"Error showing footer: {e}")
            return False

    async def take_screenshot(
        self,
        path: str,
        full_page: bool = True,
        quality: int = 90,
        hide_footer: bool = True
    ) -> str:
        """
        Take a screenshot of the current page with optional footer hiding.
        
        Args:
            path: File path to save the screenshot
            full_page: Whether to capture the full page
            quality: JPEG quality (0-100)
            hide_footer: Whether to hide footer before taking screenshot
            
        Returns:
            Path to the saved screenshot
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call setup_browser() first.")
        
        footer_was_hidden = False
        
        try:
            # Wait for page to be fully loaded
            await self.page.wait_for_load_state('networkidle', timeout=5000)
            await self.page.wait_for_timeout(500)
            
            # Hide footer if requested
            if hide_footer:
                footer_was_hidden = await self.hide_footer()
                if footer_was_hidden:
                    # Wait a moment for the layout to adjust
                    await self.page.wait_for_timeout(200)
            
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
        finally:
            # Always restore footer if it was hidden
            if hide_footer and footer_was_hidden:
                try:
                    await self.show_footer()
                except Exception as e:
                    print(f"Warning: Could not restore footer: {e}")
    
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
    
    async def save_state(self, state_file: str) -> None:
        """
        Save current browser context state to file.
        
        Args:
            state_file: Path to save the browser state
        """
        if not self.context:
            raise RuntimeError("Browser context not initialized. Call setup_browser() first.")
        
        try:
            # Ensure directory exists
            state_path = Path(state_file)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the state
            await self.context.storage_state(path=state_file)
            print(f"✓ Browser state saved to: {state_file}")
        except Exception as e:
            print(f"Error saving browser state: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()