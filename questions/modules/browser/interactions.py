"""
Common interaction patterns for browser automation.

This module provides reusable interaction methods that handle common patterns
like clicking with fallback strategies, filling forms, and waiting for elements.
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .selectors import SelectorStrategies


class InteractionHandler:
    """Handles common browser interaction patterns with fallback strategies."""
    
    def __init__(self, page: Page):
        self.page = page
        self.selectors = SelectorStrategies()
    
    async def click_with_strategies(
        self, 
        selectors: List[str], 
        timeout: int = 5000,
        description: str = "element"
    ) -> bool:
        """
        Try to click an element using multiple selectors and click strategies.
        
        Args:
            selectors: List of CSS selectors to try
            timeout: Timeout for each attempt in milliseconds
            description: Description of the element for logging
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Looking for {description}...")
        
        for selector in selectors:
            try:
                # Wait for element to be present
                element = await self.page.wait_for_selector(selector, timeout=timeout)
                
                if element:
                    # Scroll into view if needed
                    await element.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(500)
                    
                    # Try different click strategies
                    click_strategies = self.selectors.get_click_strategies()
                    
                    for i, strategy in enumerate(click_strategies, 1):
                        try:
                            print(f"Trying click strategy {i} ({strategy['name']}) for {description} using selector: {selector}")
                            
                            if strategy['force']:
                                await self.page.click(selector, force=True, timeout=timeout)
                            elif strategy['position']:
                                await self.page.click(selector, position=strategy['position'], timeout=timeout)
                            else:
                                await self.page.click(selector, timeout=timeout)
                            
                            print(f"✓ Successfully clicked {description} using selector: {selector} (strategy {i})")
                            
                            # Wait for any resulting navigation or changes
                            await self.page.wait_for_timeout(1000)
                            return True
                            
                        except Exception as click_error:
                            print(f"Click strategy {i} failed: {click_error}")
                            if i < len(click_strategies):
                                continue
                            else:
                                raise click_error
                    
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                print(f"Error with {description} selector {selector}: {e}")
                continue
                
        print(f"Could not find or click {description}")
        return False
    
    async def fill_form_field(
        self, 
        selectors: List[str], 
        value: str, 
        field_name: str = "field",
        timeout: int = 3000
    ) -> bool:
        """
        Fill a form field using multiple selector strategies.
        
        Args:
            selectors: List of CSS selectors to try
            value: Value to fill in the field
            field_name: Name of the field for logging
            timeout: Timeout for each attempt in milliseconds
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Filling {field_name} field...")
        
        for selector in selectors:
            try:
                # Wait for element to be present
                await self.page.wait_for_selector(selector, timeout=timeout)
                
                # Clear and fill using page methods
                await self.page.fill(selector, '')  # Clear field
                await self.page.fill(selector, value)  # Fill with value
                print(f"✓ {field_name.capitalize()} filled using selector: {selector}")
                return True
                
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                print(f"Error with {field_name} selector {selector}: {e}")
                continue
                
        print(f"Could not find or fill {field_name} field")
        return False
    
    async def wait_for_any_selector(
        self, 
        selectors: List[str], 
        timeout: int = 5000,
        description: str = "element"
    ) -> Optional[str]:
        """
        Wait for any of the provided selectors to appear.
        
        Args:
            selectors: List of CSS selectors to wait for
            timeout: Total timeout in milliseconds
            description: Description for logging
            
        Returns:
            The selector that was found, or None if none found
        """
        print(f"Waiting for {description}...")
        
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=timeout)
                print(f"Found {description} using selector: {selector}")
                return selector
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                print(f"Error waiting for {description} with selector {selector}: {e}")
                continue
                
        print(f"Could not find {description}")
        return None
    
    async def get_element_text(
        self, 
        selectors: List[str], 
        description: str = "element"
    ) -> Optional[str]:
        """
        Get text content from an element using multiple selectors.
        
        Args:
            selectors: List of CSS selectors to try
            description: Description for logging
            
        Returns:
            Text content if found, None otherwise
        """
        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    text = await element.text_content()
                    if text and text.strip():
                        print(f"Found {description} text using selector: {selector}")
                        return text.strip()
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                print(f"Error getting text from {description} with selector {selector}: {e}")
                continue
                
        print(f"Could not get text from {description}")
        return None
    
    async def get_element_attribute(
        self, 
        selectors: List[str], 
        attribute: str,
        description: str = "element"
    ) -> Optional[str]:
        """
        Get an attribute value from an element using multiple selectors.
        
        Args:
            selectors: List of CSS selectors to try
            attribute: Attribute name to get
            description: Description for logging
            
        Returns:
            Attribute value if found, None otherwise
        """
        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    attr_value = await element.get_attribute(attribute)
                    if attr_value is not None:
                        print(f"Found {description} {attribute} using selector: {selector}")
                        return attr_value
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                print(f"Error getting {attribute} from {description} with selector {selector}: {e}")
                continue
                
        print(f"Could not get {attribute} from {description}")
        return None
    
    async def remove_overlays(self, overlay_selectors: List[str]) -> None:
        """
        Remove overlay elements that might interfere with interactions.
        
        Args:
            overlay_selectors: List of selectors for overlay elements to remove
        """
        try:
            selectors_js = ', '.join([f'"{sel}"' for sel in overlay_selectors])
            await self.page.evaluate(f'''
                () => {{
                    const overlaySelectors = [{selectors_js}];
                    
                    overlaySelectors.forEach(selector => {{
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {{
                            if (el) {{
                                el.style.display = 'none';
                                el.style.visibility = 'hidden';
                                el.remove();
                            }}
                        }});
                    }});
                }}
            ''')
            print("Removed overlay elements")
        except Exception as e:
            print(f"Error removing overlays: {e}")
    
    async def press_key_fallback(self, selector: str, key: str, description: str = "element") -> bool:
        """
        Press a key on an element as a fallback interaction method.
        
        Args:
            selector: CSS selector for the element
            key: Key to press (e.g., 'Enter', 'Tab')
            description: Description for logging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Trying fallback: pressing {key} on {description}...")
            await self.page.press(selector, key)
            print(f"✓ {description} activated by pressing {key}")
            await self.page.wait_for_timeout(1000)
            return True
        except Exception as e:
            print(f"{key} key fallback failed: {e}")
            return False
    
    async def scroll_and_click(self, selector: str, description: str = "element") -> bool:
        """
        Scroll to an element and click it.
        
        Args:
            selector: CSS selector for the element
            description: Description for logging
            
        Returns:
            True if successful, False otherwise
        """
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if element:
                await element.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(500)
                await element.click()
                print(f"✓ Scrolled to and clicked {description}")
                return True
        except Exception as e:
            print(f"Error scrolling and clicking {description}: {e}")
            return False
    
    async def wait_for_navigation_or_timeout(self, timeout: int = 10000) -> None:
        """
        Wait for navigation to complete or timeout.
        
        Args:
            timeout: Maximum time to wait in milliseconds
        """
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
        except PlaywrightTimeoutError:
            print("Warning: Page didn't reach networkidle state, but continuing...")