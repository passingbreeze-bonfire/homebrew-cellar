"""Browser management utilities for GetCurCur."""

from typing import Optional, Any
from contextlib import contextmanager
from playwright.sync_api import sync_playwright, Browser, BrowserContext
import logging

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Manages Playwright browser instances and contexts.
    Provides context managers for efficient resource management.
    """
    
    def __init__(self, headless: bool = True, user_agent: Optional[str] = None):
        """
        Initialize browser manager.
        
        Args:
            headless: Run browser in headless mode
            user_agent: Custom user agent string
        """
        self.headless = headless
        self.user_agent = user_agent or (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        self._browser: Optional[Browser] = None
        self._playwright = None
    
    @contextmanager
    def browser_context(self):
        """
        Context manager that provides a browser context.
        Automatically manages browser and context lifecycle.
        
        Yields:
            BrowserContext: Playwright browser context
            
        Raises:
            NetworkError: If browser launch fails
            RuntimeError: If context creation fails
        """
        from getcurcur.exceptions import NetworkError
        
        with sync_playwright() as p:
            self._playwright = p
            browser = None
            context = None
            
            try:
                logger.debug(f"Launching browser (headless={self.headless})")
                try:
                    browser = p.chromium.launch(headless=self.headless)
                except Exception as e:
                    raise NetworkError(f"Failed to launch browser: {e}")
                
                try:
                    context = browser.new_context(
                        user_agent=self.user_agent,
                        viewport={'width': 1920, 'height': 1080}
                    )
                except Exception as e:
                    raise RuntimeError(f"Failed to create browser context: {e}")
                
                # Set common page settings
                try:
                    context.set_default_timeout(30000)
                    context.set_default_navigation_timeout(30000)
                except Exception as e:
                    logger.warning(f"Failed to set browser timeouts: {e}")
                
                yield context
                
            except (NetworkError, RuntimeError):
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                logger.error(f"Unexpected browser context error: {e}")
                raise RuntimeError(f"Browser context management failed: {e}")
            finally:
                # Ensure cleanup happens even if there are errors
                if context:
                    try:
                        context.close()
                        logger.debug("Browser context closed")
                    except Exception as e:
                        logger.warning(f"Failed to close browser context: {e}")
                if browser:
                    try:
                        browser.close()
                        logger.debug("Browser closed")
                    except Exception as e:
                        logger.warning(f"Failed to close browser: {e}")
    
    @contextmanager
    def shared_browser_context(self):
        """
        Context manager for shared browser instance.
        Useful when multiple operations need the same browser.
        
        Yields:
            BrowserContext: Shared browser context
        """
        if self._browser is None:
            raise RuntimeError("Shared browser not initialized. Use 'with_shared_browser' first.")
        
        context = None
        try:
            context = self._browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080}
            )
            context.set_default_timeout(30000)
            context.set_default_navigation_timeout(30000)
            
            yield context
            
        finally:
            if context:
                context.close()
    
    @contextmanager
    def with_shared_browser(self):
        """
        Context manager for shared browser lifecycle.
        Use this when you need multiple contexts with the same browser.
        
        Example:
            with browser_manager.with_shared_browser():
                with browser_manager.shared_browser_context() as ctx1:
                    # Use context 1
                with browser_manager.shared_browser_context() as ctx2:
                    # Use context 2
        """
        with sync_playwright() as p:
            try:
                logger.debug(f"Launching shared browser (headless={self.headless})")
                self._browser = p.chromium.launch(headless=self.headless)
                self._playwright = p
                
                yield
                
            finally:
                if self._browser:
                    self._browser.close()
                    self._browser = None
                    logger.debug("Shared browser closed")


# Global browser manager instance
_browser_manager = BrowserManager()


def get_browser_manager(headless: bool = True, user_agent: Optional[str] = None) -> BrowserManager:
    """
    Get or create a browser manager instance.
    
    Args:
        headless: Run browser in headless mode
        user_agent: Custom user agent string
        
    Returns:
        BrowserManager instance
    """
    global _browser_manager
    
    # Set default user agent if not provided
    if user_agent is None:
        user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
    
    # Update settings if they've changed
    if (_browser_manager.headless != headless or 
        _browser_manager.user_agent != user_agent):
        _browser_manager = BrowserManager(headless=headless, user_agent=user_agent)
    
    return _browser_manager