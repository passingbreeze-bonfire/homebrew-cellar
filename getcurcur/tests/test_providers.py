"""Tests for exchange rate providers."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from playwright.sync_api import BrowserContext
from getcurcur.providers.base import ExchangeRateProvider, CacheManager
from getcurcur.providers.korea import HanaBankProvider, WooriBankProvider
from getcurcur.exceptions import NetworkError, ParseError


class TestCacheManager:
    """Test cache manager functionality."""
    
    def test_cache_key_generation(self, tmp_path):
        """Test cache key generation."""
        cache = CacheManager(cache_dir=tmp_path / "cache", ttl_minutes=30)
        key1 = cache._get_cache_key("provider1", param1="value1")
        key2 = cache._get_cache_key("provider1", param1="value1")
        key3 = cache._get_cache_key("provider2", param1="value1")
        
        assert key1 == key2  # Same parameters should generate same key
        assert key1 != key3  # Different provider should generate different key
    
    def test_cache_miss(self, tmp_path):
        """Test cache miss scenario."""
        cache = CacheManager(cache_dir=tmp_path / "cache", ttl_minutes=30)
        result = cache.get("non_existent_provider")
        assert result is None
    
    def test_cache_hit(self, tmp_path):
        """Test cache hit scenario."""
        cache = CacheManager(cache_dir=tmp_path / "cache", ttl_minutes=30)
        test_data = [{"code": "USD", "rate": "1300"}]
        
        # Set cache
        cache.set("test_provider", test_data)
        
        # Get from cache
        result = cache.get("test_provider")
        assert result == test_data


class TestExchangeRateProvider:
    """Test base provider functionality."""
    
    def test_abstract_methods(self):
        """Test that abstract methods must be implemented."""
        with pytest.raises(TypeError):
            ExchangeRateProvider()
    
    def test_convert_amount(self):
        """Test currency conversion."""
        # Create a mock provider
        class MockProvider(ExchangeRateProvider):
            def get_provider_name(self):
                return "Mock Provider"
            
            def get_country(self):
                return "KR"
            
            def fetch_rates(self, context):
                return [
                    {"code": "USD", "cash_buy": "1,300.00", "cash_sell": "1,350.00"},
                    {"code": "EUR", "cash_buy": "1,400.00", "cash_sell": "1,450.00"}
                ]
        
        provider = MockProvider(cache_enabled=False)

        mock_context = MagicMock()

        # Test USD to KRW conversion
        result = provider.convert_amount(amount=100, from_currency="USD", context=mock_context, to_currency="KRW", transaction_type="cash_buy")
        assert result == 130000.0
        
        # Test with sell rate
        result = provider.convert_amount(amount=100, from_currency="USD", context=mock_context, to_currency="KRW", transaction_type="cash_sell")
        assert result == 135000.0
        
        # Test with non-existent currency
        result = provider.convert_amount(amount=100, from_currency="GBP", context=mock_context , to_currency="KRW", transaction_type="cash_buy")
        assert result is None


class TestHanaBankProvider:
    """Test Hana Bank provider."""
    
    def test_fetch_rates_success(self):
        """Test successful rate fetching."""
        # Setup mock page with content
        mock_page = MagicMock()
        mock_page.content.return_value = """
        <html>
            <table id="p_grid1_tb">
                <tbody>
                    <tr>
                        <td>미국</td>
                        <td>USD</td>
                        <td>1,300.00</td>
                        <td>1,320.00</td>
                        <td>1,350.00</td>
                    </tr>
                </tbody>
            </table>
        </html>
        """
        
        # Setup mock context
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        # Test with mock context
        provider = HanaBankProvider()
        rates = provider.fetch_rates(mock_context)
        
        assert len(rates) == 1
        assert rates[0]["code"] == "USD"
        assert rates[0]["cash_buy"] == "1,300.00"
        assert rates[0]["cash_sell"] == "1,350.00"
        assert rates[0]["provider"] == "KEB Hana Bank (Korea)"
        assert rates[0]["country"] == "KR"
    
    def test_provider_metadata(self):
        """Test provider metadata."""
        provider = HanaBankProvider()
        assert provider.get_provider_name() == "KEB Hana Bank (Korea)"
        assert provider.get_country() == "KR"


class TestProviderIntegration:
    """Integration tests for providers."""
    
    @pytest.mark.skip(reason="Requires actual network access")
    def test_real_hana_bank_fetch(self):
        """Test actual Hana Bank website fetching."""
        provider = HanaBankProvider(cache_enabled=False)
        rates = provider.fetch_rates()
        
        # Should have some rates
        assert len(rates) > 0
        
        # Check USD is present
        usd_rates = [r for r in rates if r["code"] == "USD"]
        assert len(usd_rates) > 0
        
        # Check rate format
        usd_rate = usd_rates[0]
        assert "cash_buy" in usd_rate
        assert "cash_sell" in usd_rate
        assert usd_rate["provider"] == "KEB Hana Bank (Korea)"
        assert usd_rate["country"] == "KR"


class TestBrowserManager:
    """Test browser manager functionality."""
    
    @patch('getcurcur.browser_manager.sync_playwright')
    def test_browser_context_manager(self, mock_playwright):
        """Test browser context manager lifecycle."""
        from getcurcur.browser_manager import BrowserManager
        
        # Setup mocks
        mock_context = MagicMock()
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_chromium = MagicMock()
        mock_chromium.launch.return_value = mock_browser
        
        mock_p = MagicMock()
        mock_p.chromium = mock_chromium
        mock_playwright.return_value.__enter__.return_value = mock_p
        
        # Test context manager
        manager = BrowserManager(headless=True)
        with manager.browser_context() as context:
            assert context == mock_context
        
        # Verify proper cleanup
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
    
    @patch('getcurcur.browser_manager.sync_playwright')
    def test_browser_context_with_custom_user_agent(self, mock_playwright):
        """Test browser context with custom user agent."""
        from getcurcur.browser_manager import BrowserManager
        
        # Setup mocks
        mock_context = MagicMock()
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_chromium = MagicMock()
        mock_chromium.launch.return_value = mock_browser
        
        mock_p = MagicMock()
        mock_p.chromium = mock_chromium
        mock_playwright.return_value.__enter__.return_value = mock_p
        
        # Test with custom user agent
        custom_ua = "Custom User Agent"
        manager = BrowserManager(headless=False, user_agent=custom_ua)
        
        with manager.browser_context():
            pass
        
        # Verify browser launched with correct settings
        mock_chromium.launch.assert_called_with(headless=False)
        mock_browser.new_context.assert_called_with(
            user_agent=custom_ua,
            viewport={'width': 1920, 'height': 1080}
        )
    
    def test_get_browser_manager_singleton(self):
        """Test get_browser_manager returns configured instance."""
        from getcurcur.browser_manager import get_browser_manager
        
        # Test default settings
        manager1 = get_browser_manager()
        manager2 = get_browser_manager()
        assert manager1 is manager2
        
        # Test with different settings
        custom_ua = "Test Agent"
        manager3 = get_browser_manager(headless=False, user_agent=custom_ua)
        assert manager3.headless is False
        assert manager3.user_agent == custom_ua


class TestWooriBankProvider:
    """Test Woori Bank provider."""
    
    def test_provider_metadata(self):
        """Test provider metadata."""
        from getcurcur.providers.korea import WooriBankProvider
        provider = WooriBankProvider()
        assert provider.get_provider_name() == "Woori Bank (Korea)"
        assert provider.get_country() == "KR"

    def test_fetch_rates_success(self):
        """Test successful rate fetching."""
        from getcurcur.providers.korea import WooriBankProvider
        
        # Setup mock page with realistic Woori Bank HTML structure
        mock_page = MagicMock()
        mock_page.content.return_value = """
        <html>
            <table class="table_type01">
                <tbody>
                    <tr>
                        <td>USD</td>
                        <td>미국 달러</td>
                        <td>1,305.00</td>
                        <td>1,325.00</td>
                        <td>1,355.00</td>
                    </tr>
                    <tr>
                        <td>EUR</td>
                        <td>유럽연합 유로</td>
                        <td>1,405.00</td>
                        <td>1,425.00</td>
                        <td>1,455.00</td>
                    </tr>
                </tbody>
            </table>
        </html>
        """
        
        # Setup mock context
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        
        # Test
        provider = WooriBankProvider(cache_enabled=False)
        rates = provider.fetch_rates(mock_context)
        
        assert len(rates) == 2
        assert rates[0]["code"] == "USD"
        assert rates[0]["currency"] == "미국 달러"
        assert rates[0]["cash_buy"] == "1,305.00"
        assert rates[0]["cash_sell"] == "1,355.00"
        assert rates[0]["provider"] == "Woori Bank (Korea)"
        assert rates[0]["country"] == "KR"


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_network_error_handling(self):
        """Test network error handling."""
        from getcurcur.exceptions import NetworkError
        
        class FailingProvider(ExchangeRateProvider):
            def get_provider_name(self):
                return "Failing Provider"
            
            def get_country(self):
                return "KR"
            
            def fetch_rates(self, context):
                raise NetworkError("Connection timeout")
        
        provider = FailingProvider(cache_enabled=False)
        
        with pytest.raises(NetworkError):
            mock_context = MagicMock()
            provider.get_rates(mock_context, use_cache=False)
    
    def test_parse_error_handling(self):
        """Test parsing error handling."""
        from getcurcur.exceptions import ParseError
        
        class ParseFailingProvider(ExchangeRateProvider):
            def get_provider_name(self):
                return "Parse Failing Provider"
            
            def get_country(self):
                return "KR"
            
            def fetch_rates(self, context):
                raise ParseError("Failed to parse exchange rates")
        
        provider = ParseFailingProvider(cache_enabled=False)
        
        with pytest.raises(ParseError):
            mock_context = MagicMock()
            provider.get_rates(mock_context, use_cache=False)


class TestCacheIntegration:
    """Test cache integration with providers."""
    
    def test_cache_hit_scenario(self, tmp_path):
        """Test successful cache retrieval."""
        from getcurcur.providers.base import CacheManager
        
        # Create cache with test data
        cache = CacheManager(cache_dir=tmp_path / "cache", ttl_minutes=30)
        test_data = [{"code": "USD", "rate": "1300.00", "provider": "Test"}]
        cache.set("test_provider", test_data)
        
        # Create provider with cache
        class TestProvider(ExchangeRateProvider):
            def __init__(self):
                super().__init__(cache_enabled=True, cache_ttl=30)
                self.cache_manager = cache
            
            def get_provider_name(self):
                return "test_provider"
            
            def get_country(self):
                return "KR"
            
            def fetch_rates(self, context):
                return [{"code": "USD", "rate": "1301.00", "provider": "Test"}]
        
        provider = TestProvider()
        mock_context = MagicMock()
        
        # Should return cached data
        result = provider.get_rates(mock_context, use_cache=True)
        assert result == test_data
        assert result[0]["rate"] == "1300.00"  # Cached value, not fresh
    
    def test_cache_miss_fetch_fresh(self, tmp_path):
        """Test fresh data fetch on cache miss."""
        from getcurcur.providers.base import CacheManager
        
        cache = CacheManager(cache_dir=tmp_path / "cache", ttl_minutes=30)
        
        class TestProvider(ExchangeRateProvider):
            def __init__(self):
                super().__init__(cache_enabled=True, cache_ttl=30)
                self.cache_manager = cache
            
            def get_provider_name(self):
                return "test_provider_fresh"
            
            def get_country(self):
                return "KR"
            
            def fetch_rates(self, context):
                return [{"code": "USD", "rate": "1301.00", "provider": "Test"}]
        
        provider = TestProvider()
        mock_context = MagicMock()
        
        # Should fetch fresh data (cache miss)
        result = provider.get_rates(mock_context, use_cache=True)
        assert result[0]["rate"] == "1301.00"  # Fresh value
        
        # Verify data was cached
        cached_result = cache.get("test_provider_fresh")
        assert cached_result == result
