"""
Navigation workflow for Zanichelli exercise automation.

This module handles navigation between exercises, questions, and pages.
"""

from typing import List, Dict, Any, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..browser.interactions import InteractionHandler
from ..browser.selectors import SelectorStrategies
from ..content.processor import ContentProcessor


class NavigationWorkflow:
    """Handles navigation workflows for exercises and questions."""
    
    def __init__(self, page: Page):
        self.page = page
        self.interactions = InteractionHandler(page)
        self.selectors = SelectorStrategies()
        self.processor = ContentProcessor(page)
    
    async def get_exercise_cards(self) -> List[Any]:
        """
        Get all exercise cards from the page.
        
        Returns:
            List of exercise card elements
        """
        print("Looking for exercise cards...")
        
        # Wait for z-card elements to load
        try:
            await self.page.wait_for_selector('z-card', timeout=10000)
        except PlaywrightTimeoutError:
            print("Warning: z-card elements not found")
        
        card_selectors = self.selectors.get_selectors('EXERCISE_CARDS')
        
        for selector in card_selectors:
            try:
                cards = await self.page.query_selector_all(selector)
                if cards:
                    print(f"Found {len(cards)} exercise cards using selector: {selector}")
                    
                    # Log the exercise titles for debugging
                    await self._log_exercise_titles(cards)
                    
                    return cards
            except Exception as e:
                print(f"Error with card selector {selector}: {e}")
                continue
        
        # Fallback: look for any elements containing Anteprima buttons
        try:
            anteprima_buttons = await self.page.query_selector_all('button:has-text("Anteprima"), button:has-text("ANTEPRIMA")')
            if anteprima_buttons:
                print(f"Found {len(anteprima_buttons)} Anteprima buttons as fallback")
                return anteprima_buttons
        except Exception as e:
            print(f"Fallback search failed: {e}")
        
        raise Exception("Could not find any exercise cards or Anteprima buttons")
    
    async def _log_exercise_titles(self, cards: List[Any]) -> None:
        """Log exercise titles for debugging."""
        for i, card in enumerate(cards):
            try:
                # Look for the exercise title in the text slot
                title_element = await card.query_selector('[slot="text"] .body-2-sb, [slot="text"] div:first-child')
                if title_element:
                    title = await title_element.text_content()
                    print(f"  Exercise {i+1}: {title.strip() if title else 'No title'}")
            except Exception as e:
                print(f"  Exercise {i+1}: Could not extract title - {e}")
    
    async def click_anteprima_button(self, exercise_index: int = 0) -> bool:
        """
        Locate and click the ANTEPRIMA button for a specific exercise.
        
        Args:
            exercise_index: Index of the exercise to click (0-based)
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Looking for ANTEPRIMA button for exercise {exercise_index + 1}...")
        
        # Get all exercise cards or ANTEPRIMA buttons
        cards = await self.get_exercise_cards()
        
        if exercise_index >= len(cards):
            raise Exception(f"Exercise index {exercise_index} is out of range. Found {len(cards)} exercises.")
        
        target_card = cards[exercise_index]
        
        # Try to find Anteprima button within the card
        anteprima_selectors = self.selectors.get_selectors('ANTEPRIMA_BUTTON')
        
        for selector in anteprima_selectors:
            try:
                # Look for the button within this specific card
                button = await target_card.query_selector(selector)
                if button:
                    # Get the exercise title for logging
                    title = await self._get_exercise_title_from_card(target_card, exercise_index)
                    
                    # Scroll into view if needed
                    await button.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(500)
                    
                    # Click the button
                    await button.click()
                    print(f"✓ Successfully clicked Anteprima button for: {title}")
                    
                    # Wait for modal/drawer to open
                    await self.page.wait_for_timeout(2000)
                    return True
                    
            except Exception as e:
                print(f"Error with Anteprima selector {selector}: {e}")
                continue
        
        # If we couldn't find button within card, try clicking the card itself if it's clickable
        try:
            await target_card.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(500)
            await target_card.click()
            print(f"✓ Clicked exercise card {exercise_index + 1} directly")
            await self.page.wait_for_timeout(2000)
            return True
        except Exception as e:
            print(f"Error clicking card directly: {e}")
        
        raise Exception(f"Could not click ANTEPRIMA button for exercise {exercise_index + 1}")
    
    async def _get_exercise_title_from_card(self, card: Any, exercise_index: int) -> str:
        """Get exercise title from a card element."""
        try:
            title_element = await card.query_selector('[slot="text"] .body-2-sb, [slot="text"] div:first-child')
            title = await title_element.text_content() if title_element else f"Exercise {exercise_index + 1}"
            return title.strip() if title else f"Exercise {exercise_index + 1}"
        except:
            return f"Exercise {exercise_index + 1}"
    
    async def click_svolgi_button(self) -> bool:
        """
        Locate and click the 'SVOLGI' button in the modal/drawer.
        
        Returns:
            True if successful, False otherwise
        """
        print("Looking for SVOLGI button in modal...")
        
        # Wait for modal to appear
        await self.page.wait_for_timeout(1000)
        
        svolgi_selectors = self.selectors.get_selectors('SVOLGI_BUTTON')
        
        success = await self.interactions.click_with_strategies(
            selectors=svolgi_selectors,
            timeout=5000,
            description="SVOLGI button"
        )
        
        if success:
            # Wait for navigation to complete
            await self.interactions.wait_for_navigation_or_timeout(15000)
        
        return success
    
    async def click_inizia_button(self) -> bool:
        """
        Locate and click the 'INIZIA' button on the instruction page.
        
        Returns:
            True if successful, False otherwise
        """
        print("Looking for INIZIA button on instruction page...")
        
        # Wait a bit for the instruction page to load
        await self.page.wait_for_timeout(2000)
        
        inizia_selectors = self.selectors.get_selectors('INIZIA_BUTTON')
        
        success = await self.interactions.click_with_strategies(
            selectors=inizia_selectors,
            timeout=5000,
            description="INIZIA button"
        )
        
        if not success:
            # Fallback: try pressing Enter on the page
            try:
                print("Trying fallback: pressing Enter to start exercise...")
                await self.page.press('body', 'Enter')
                print("✓ Exercise started by pressing Enter")
                await self.interactions.wait_for_navigation_or_timeout(15000)
                return True
            except Exception as e:
                print(f"Enter key fallback failed: {e}")
                return False
        else:
            # Wait for navigation to exercise page
            await self.interactions.wait_for_navigation_or_timeout(15000)
        
        return success
    
    async def navigate_to_next_question(self) -> bool:
        """
        Navigate to the next question using data-index navigation.
        
        Returns:
            True if successful, False otherwise
        """
        print("Navigating to next question...")
        
        try:
            # Get current question number (1-based)
            current_num = await self.processor.get_current_question_number()
            next_num = current_num + 1
            
            # Convert to 0-based data-index for next question
            next_data_index = next_num - 1
            
            print(f"Looking for question {next_num} (data-index={next_data_index})")
            
            # Look for div with the next data-index and click the <a> inside
            next_question_selectors = self.selectors.create_data_index_selector(next_data_index)
            
            for selector in next_question_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.scroll_into_view_if_needed()
                        await self.page.wait_for_timeout(500)
                        await element.click()
                        print(f"✓ Clicked next question link using selector: {selector}")
                        
                        # Wait for question to load
                        await self.page.wait_for_timeout(2000)
                        return True
                        
                except PlaywrightTimeoutError:
                    continue
                except Exception as e:
                    print(f"Error with next question selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error getting current question number: {e}")
        
        # Fallback: try traditional navigation methods
        print("Trying fallback navigation methods...")
        fallback_selectors = self.selectors.get_selectors('NEXT_QUESTION_NAVIGATION')
        
        for selector in fallback_selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element:
                    await element.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(500)
                    await element.click()
                    print(f"✓ Clicked fallback navigation using selector: {selector}")
                    
                    # Wait for page to load
                    await self.page.wait_for_timeout(2000)
                    return True
                    
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                print(f"Error with fallback selector {selector}: {e}")
                continue
        
        print("❌ Could not navigate to next question")
        return False
    
    async def click_termina_prova_button(self) -> bool:
        """
        Click the TERMINA PROVA button on the last question.
        
        Returns:
            True if successful, False otherwise
        """
        print("Looking for TERMINA PROVA button...")
        
        termina_selectors = self.selectors.get_selectors('TERMINA_PROVA_BUTTON')
        
        success = await self.interactions.click_with_strategies(
            selectors=termina_selectors,
            timeout=5000,
            description="TERMINA PROVA button"
        )
        
        if success:
            # Wait for completion page or navigation
            await self.interactions.wait_for_navigation_or_timeout(15000)
        
        return success
    
    async def get_exercise_title(self, exercise_index: int = 0) -> str:
        """
        Get the title of the exercise for screenshot naming.
        
        Args:
            exercise_index: Index of the exercise (0-based)
            
        Returns:
            Exercise title string
        """
        try:
            cards = await self.get_exercise_cards()
            if exercise_index < len(cards):
                target_card = cards[exercise_index]
                
                # Look for title elements within the z-card structure
                title_selectors = self.selectors.get_selectors('CARD_TITLE')
                
                for selector in title_selectors:
                    title_element = await target_card.query_selector(selector)
                    if title_element:
                        title = await title_element.text_content()
                        if title and title.strip():
                            # Clean up title for filename
                            clean_title = self._clean_title_for_filename(title.strip())
                            return clean_title[:100]  # Limit length
                            
        except Exception as e:
            print(f"Error getting exercise title: {e}")
        
        return f"Exercise_{exercise_index + 1}"
    
    def _clean_title_for_filename(self, title: str) -> str:
        """Clean title for use in filenames."""
        clean_title = title.replace('/', '-').replace('\\', '-')
        clean_title = clean_title.replace(':', '-').replace('?', '').replace('*', '')
        clean_title = clean_title.replace('<', '').replace('>', '').replace('|', '-')
        clean_title = clean_title.replace('"', '').replace("'", '')
        return clean_title
    
    async def navigate_back_to_exercise_list(self, url: str) -> bool:
        """
        Navigate back to the exercise list page.
        
        Args:
            url: URL of the exercise list page
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Navigating back to exercise list...")
            
            # Try browser back button first
            try:
                await self.page.go_back()
                await self.interactions.wait_for_navigation_or_timeout(10000)
                
                # Check if we're back on the exercise list
                current_url = self.page.url
                if url in current_url:
                    print("✓ Successfully navigated back using browser back button")
                    return True
            except Exception as e:
                print(f"Browser back failed: {e}")
            
            # Fallback: navigate directly to URL
            await self.page.goto(url, wait_until='networkidle')
            print("✓ Successfully navigated back to exercise list")
            return True
            
        except Exception as e:
            print(f"Error navigating back to exercise list: {e}")
            return False
    
    async def wait_for_page_load(self, timeout: int = 10000) -> None:
        """
        Wait for page to load completely.
        
        Args:
            timeout: Maximum time to wait in milliseconds
        """
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
            await self.page.wait_for_timeout(1000)  # Additional buffer
        except PlaywrightTimeoutError:
            print("Warning: Page load timeout, but continuing...")