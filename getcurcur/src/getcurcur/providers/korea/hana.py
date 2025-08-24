from typing import List, Dict
from playwright.sync_api import Page, BrowserContext
from bs4 import BeautifulSoup
import logging

from ..base import ExchangeRateProvider

logger = logging.getLogger(__name__)


class HanaBankProvider(ExchangeRateProvider):
    """하나은행 웹사이트에서 환율 정보를 가져오는 Provider입니다."""
    
    URL = "https://www.kebhana.com/cont/mall/mall15/mall1501/index.jsp"
    
    def __init__(self, headless: bool = True, timeout: int = 30000, cache_enabled: bool = True):
        """
        Initialize HanaBankProvider.
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
            cache_enabled: Enable caching of exchange rates
        """
        super().__init__(cache_enabled=cache_enabled)
        self.headless = headless
        self.timeout = timeout

    def get_provider_name(self) -> str:
        return "KEB Hana Bank (Korea)"
    
    def get_country(self) -> str:
        return "KR"
    
    def _parse_exchange_table(self, page: Page) -> List[Dict[str, str]]:
        """Parse exchange rate table from the page."""
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        results = []
        rows = soup.select("#p_grid1_tb > tbody > tr")
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                try:
                    # Extract and clean data
                    currency_name = cols[0].text.strip()
                    currency_code = cols[1].text.strip()
                    cash_buy = cols[2].text.strip()
                    cash_sell = cols[4].text.strip()
                    
                    # Skip if no valid data
                    if not currency_code or currency_code == "-":
                        continue
                        
                    results.append({
                        "currency": currency_name,
                        "code": currency_code,
                        "cash_buy": cash_buy,
                        "cash_sell": cash_sell,
                        "provider": self.get_provider_name(),
                        "country": self.get_country()
                    })
                except (IndexError, AttributeError) as e:
                    logger.warning(f"Failed to parse row: {e}")
                    continue
        
        return results

    def fetch_rates(self, context: BrowserContext) -> List[Dict[str, str]]:
        """Fetch exchange rates using a given Playwright context."""
        from ...exceptions import NetworkError, ParseError, TimeoutError as GetCurCurTimeoutError
        
        results = []
        page = context.new_page()
        try:
            # Set timeout
            page.set_default_timeout(self.timeout)
            
            # Navigate to the page
            logger.info(f"Fetching rates from {self.URL}")
            try:
                page.goto(self.URL, wait_until="networkidle")
            except Exception as e:
                raise NetworkError(f"Failed to navigate to {self.URL}: {e}")
            
            # Wait for the exchange rate table to load
            try:
                page.wait_for_selector("#p_grid1_tb > tbody > tr", timeout=10000)
            except Exception as e:
                raise GetCurCurTimeoutError(f"Timeout waiting for exchange rate table: {e}")
            
            # Parse the exchange table
            try:
                results = self._parse_exchange_table(page)
            except Exception as e:
                raise ParseError(f"Failed to parse exchange rate data: {e}")
            
            if not results:
                raise ParseError("No exchange rate data found")
            
            logger.info(f"Successfully fetched {len(results)} exchange rates")
        finally:
            page.close()

        return results
