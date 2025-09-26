"""
Login workflow for Zanichelli exercise automation.

This module handles the complete login process including cookie acceptance,
form filling, and authentication.
"""

from typing import Optional
from playwright.async_api import Page

from ..browser.interactions import InteractionHandler
from ..browser.selectors import SelectorStrategies
from ..config.manager import ConfigManager


class LoginWorkflow:
    """Handles the complete login workflow."""
    
    def __init__(self, page: Page, config_manager: ConfigManager):
        self.page = page
        self.config_manager = config_manager
        self.interactions = InteractionHandler(page)
        self.selectors = SelectorStrategies()
    
    async def perform_complete_login(self) -> bool:
        """
        Perform the complete login process.
        
        Returns:
            True if successful, False otherwise
        """
        print("Starting complete login process...")
        
        try:
            # Step 1: Accept cookies if banner appears
            await self.accept_cookies()
            
            # Step 2: Click main ENTRA button to open login modal
            if not await self.click_entra_button():
                return False
            
            # Step 3: Fill login form with credentials
            if not await self.fill_login_form():
                return False
            
            # Step 4: Submit the form
            if not await self.submit_login_form():
                return False
            
            print("✅ Complete login process completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Login process failed: {e}")
            return False
    
    async def accept_cookies(self) -> bool:
        """
        Accept cookies if a cookie banner appears.
        
        Returns:
            True if cookies were accepted or no banner found, False on error
        """
        print("Checking for cookie banner...")
        
        cookie_selectors = self.selectors.get_selectors('COOKIE_ACCEPT')
        
        for selector in cookie_selectors:
            try:
                # Wait briefly for the element to appear
                await self.page.wait_for_selector(selector, timeout=3000)
                await self.page.click(selector)
                print(f"✓ Clicked cookie acceptance button: {selector}")
                await self.page.wait_for_timeout(1000)  # Wait for banner to disappear
                return True
            except Exception as e:
                print(f"Error with cookie selector {selector}: {e}")
                continue
        
        print("No cookie banner found or already accepted")
        return True
    
    async def click_entra_button(self) -> bool:
        """
        Click the main ENTRA button to open login modal.
        
        Returns:
            True if successful, False otherwise
        """
        entra_selectors = self.selectors.get_selectors('ENTRA_BUTTON')
        
        success = await self.interactions.click_with_strategies(
            selectors=entra_selectors,
            timeout=5000,
            description="main ENTRA button"
        )
        
        if success:
            # Wait for login modal to open
            await self.page.wait_for_timeout(2000)
        
        return success
    
    async def fill_login_form(self) -> bool:
        """
        Fill the login form with credentials from config.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.config_manager.is_loaded():
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        
        credentials = self.config_manager.get_credentials()
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            raise RuntimeError("Username or password not found in config file")
        
        print("Filling login form...")
        
        # Fill username/email field
        username_selectors = self.selectors.get_selectors('USERNAME_FIELD')
        username_success = await self.interactions.fill_form_field(
            selectors=username_selectors,
            value=username,
            field_name="username",
            timeout=3000
        )
        
        if not username_success:
            print("❌ Could not fill username field")
            return False
        
        # Fill password field
        password_selectors = self.selectors.get_selectors('PASSWORD_FIELD')
        password_success = await self.interactions.fill_form_field(
            selectors=password_selectors,
            value=password,
            field_name="password",
            timeout=3000
        )
        
        if not password_success:
            print("❌ Could not fill password field")
            return False
        
        return True
    
    async def submit_login_form(self) -> bool:
        """
        Submit the login form by clicking the ENTRA button in the modal.
        
        Returns:
            True if successful, False otherwise
        """
        print("Submitting login form...")
        
        submit_selectors = self.selectors.get_selectors('LOGIN_SUBMIT')
        
        success = await self.interactions.click_with_strategies(
            selectors=submit_selectors,
            timeout=5000,
            description="login submit button"
        )
        
        if success:
            # Wait for login to complete
            await self.page.wait_for_timeout(3000)
            
            # Wait for potential navigation or modal to close
            await self.interactions.wait_for_navigation_or_timeout(10000)
        else:
            # Final fallback: try to submit form by pressing Enter on password field
            try:
                print("Trying fallback: pressing Enter on password field...")
                password_selector = 'input[type="password"]'
                success = await self.interactions.press_key_fallback(
                    selector=password_selector,
                    key='Enter',
                    description="password field"
                )
                
                if success:
                    await self.page.wait_for_timeout(3000)
                    await self.interactions.wait_for_navigation_or_timeout(10000)
                
            except Exception as e:
                print(f"Enter key fallback failed: {e}")
                return False
        
        return success
    
    async def remove_cookie_banners(self) -> None:
        """Remove cookie banners and overlays using JavaScript injection."""
        cookie_selectors = self.selectors.get_selectors('COOKIE_BANNER_ELEMENTS')
        await self.interactions.remove_overlays(cookie_selectors)
    
    async def verify_login_success(self) -> bool:
        """
        Verify that login was successful by checking for login indicators.
        
        Returns:
            True if login appears successful, False otherwise
        """
        try:
            # Wait a moment for page to update
            await self.page.wait_for_timeout(2000)
            
            # Check if we're still on a login page or if login modal is still visible
            login_indicators = [
                'button:has-text("ENTRA")',
                'input[type="password"]',
                '.login-modal',
                '.auth-modal'
            ]
            
            for indicator in login_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=2000)
                    if element and await element.is_visible():
                        print(f"Login may have failed - still seeing: {indicator}")
                        return False
                except:
                    continue
            
            # Check for success indicators
            success_indicators = [
                ':has-text("Benvenuto")',
                ':has-text("Dashboard")',
                ':has-text("Profilo")',
                '.user-menu',
                '.logout-btn'
            ]
            
            for indicator in success_indicators:
                try:
                    element = await self.page.wait_for_selector(indicator, timeout=2000)
                    if element and await element.is_visible():
                        print(f"✓ Login success indicator found: {indicator}")
                        return True
                except:
                    continue
            
            # If no clear indicators, assume success if we got this far
            print("No clear login indicators found, assuming success")
            return True
            
        except Exception as e:
            print(f"Error verifying login success: {e}")
            return True  # Assume success to continue
    
    async def handle_login_errors(self) -> Optional[str]:
        """
        Check for and handle common login errors.
        
        Returns:
            Error message if found, None otherwise
        """
        error_selectors = [
            ':has-text("Credenziali non valide")',
            ':has-text("Username o password errati")',
            ':has-text("Accesso negato")',
            ':has-text("Account bloccato")',
            '.error-message',
            '.login-error',
            '.alert-danger'
        ]
        
        for selector in error_selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=1000)
                if element and await element.is_visible():
                    error_text = await element.text_content()
                    return error_text.strip() if error_text else "Login error detected"
            except:
                continue
        
        return None
    
    async def logout(self) -> bool:
        """
        Perform logout if needed.
        
        Returns:
            True if successful or not needed, False on error
        """
        logout_selectors = [
            'button:has-text("Logout")',
            'button:has-text("Esci")',
            'a:has-text("Logout")',
            'a:has-text("Esci")',
            '.logout-btn',
            '.user-menu button:has-text("Esci")'
        ]
        
        for selector in logout_selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=2000)
                if element and await element.is_visible():
                    await element.click()
                    print("✓ Logged out successfully")
                    await self.page.wait_for_timeout(2000)
                    return True
            except:
                continue
        
        print("No logout button found or already logged out")
        return True