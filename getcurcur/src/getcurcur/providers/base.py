from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_fixed
from playwright.sync_api import BrowserContext

import json
import hashlib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Simple cache manager for exchange rates."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_minutes: int = 30):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_minutes: Cache time-to-live in minutes
        """
        self.cache_dir = cache_dir or Path.home() / ".getcurcur" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def _get_cache_key(self, provider_name: str, **kwargs) -> str:
        """Generate cache key based on provider and parameters."""
        key_data = f"{provider_name}_{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, provider_name: str, **kwargs) -> Optional[List[Dict[str, Any]]]:
        """Get cached data if available and not expired."""
        from ..exceptions import CacheError
        
        cache_key = self._get_cache_key(provider_name, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Validate cache data structure
            if 'timestamp' not in cache_data or 'data' not in cache_data:
                logger.warning(f"Invalid cache data structure for {provider_name}")
                cache_file.unlink()  # Remove corrupted cache
                return None
            
            try:
                cached_time = datetime.fromisoformat(cache_data['timestamp'])
            except ValueError as e:
                logger.warning(f"Invalid timestamp in cache for {provider_name}: {e}")
                cache_file.unlink()  # Remove corrupted cache
                return None
            
            if datetime.now() - cached_time > self.ttl:
                logger.debug(f"Cache expired for {provider_name}")
                try:
                    cache_file.unlink()
                except OSError as e:
                    logger.warning(f"Failed to remove expired cache file: {e}")
                return None
            
            logger.debug(f"Cache hit for {provider_name}")
            return cache_data['data']
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read cache for {provider_name}: {e}")
            try:
                cache_file.unlink()  # Remove corrupted cache
            except OSError:
                pass  # Ignore if we can't remove the file
            return None
        except Exception as e:
            # For unexpected errors, raise CacheError
            raise CacheError(f"Unexpected error reading cache for {provider_name}: {e}")
    
    def set(self, provider_name: str, data: List[Dict[str, Any]], **kwargs):
        """Save data to cache."""
        from ..exceptions import CacheError
        
        if not data:
            logger.warning(f"Attempted to cache empty data for {provider_name}")
            return
        
        cache_key = self._get_cache_key(provider_name, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'provider': provider_name,
                'data': data
            }
            
            # Write to temporary file first, then atomic move
            temp_file = cache_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # Atomic move to prevent corrupted cache files
            temp_file.rename(cache_file)
            logger.debug(f"Cached data for {provider_name}")
            
        except (OSError, json.JSONEncodeError) as e:
            logger.warning(f"Failed to write cache for {provider_name}: {e}")
            # Clean up temp file if it exists
            temp_file = cache_file.with_suffix('.tmp')
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
        except Exception as e:
            # For unexpected errors, raise CacheError
            raise CacheError(f"Unexpected error writing cache for {provider_name}: {e}")


class ExchangeRateProvider(ABC):
    """
    Base class for all exchange rate providers.
    Supports caching, retry logic, and country-specific information.
    """

    def __init__(self, cache_enabled: bool = True, cache_ttl: int = 30):
        """
        Initialize provider with optional caching.
        
        Args:
            cache_enabled: Enable caching of exchange rates
            cache_ttl: Cache time-to-live in minutes
        """
        self.cache_enabled = cache_enabled
        self.cache_manager = CacheManager(ttl_minutes=cache_ttl) if cache_enabled else None
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'Hana Bank')."""
        pass
    
    @abstractmethod
    def get_country(self) -> str:
        """Return the country code (e.g., 'KR' for Korea)."""
        pass
    
    @abstractmethod
    def fetch_rates(self, context: BrowserContext) -> List[Dict[str, str]]:
        """
        Fetch exchange rates from the provider.
        
        Returns:
            List of dictionaries containing exchange rate information:
            - currency: Currency name
            - code: Currency code (e.g., USD, EUR)
            - cash_buy: Buying rate for cash
            - cash_sell: Selling rate for cash
            - provider: Provider name
            - country: Country code
        """
        pass
    
    def get_rates(self, context: BrowserContext, use_cache: bool = True) -> List[Dict[str, str]]:
        """
        Get exchange rates with optional caching.
        
        Args:
            context: Playwright browser context
            use_cache: Whether to use cached data if available
        
        Returns:
            List of exchange rate dictionaries
        """
        if use_cache and self.cache_enabled and self.cache_manager:
            cached_data = self.cache_manager.get(self.get_provider_name())
            if cached_data:
                return cached_data
        
        # Fetch fresh data with retry logic
        @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
        def _fetch_with_retry():
            return self.fetch_rates(context)
        
        try:
            rates = _fetch_with_retry()
            
            # Cache the results
            if self.cache_enabled and self.cache_manager and rates:
                self.cache_manager.set(self.get_provider_name(), rates)
            
            return rates
        except Exception as e:
            logger.error(f"Failed to fetch rates from {self.get_provider_name()}: {e}")
            raise
    
    def convert_amount(self, amount: float, from_currency: str, 
                      context: BrowserContext, to_currency: str = "KRW", 
                      transaction_type: str = "cash_buy") -> Optional[float]:
        """
        Convert amount between currencies.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            context: Browser context for rate fetching
            to_currency: Target currency code (default: KRW)
            transaction_type: Either 'cash_buy' or 'cash_sell'
        
        Returns:
            Converted amount or None if conversion not possible
        """
        from ..exceptions import ProviderError
        
        # Validate inputs
        if amount < 0:
            raise ValueError("Amount cannot be negative.")
        if transaction_type not in ["cash_buy", "cash_sell"]:
            raise ValueError(f"Invalid transaction_type: {transaction_type}. Must be 'cash_buy' or 'cash_sell'.")

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        try:
            rates = self.get_rates(context)
        except Exception as e:
            raise ProviderError(f"Failed to fetch exchange rates: {e}")
        
        if not rates:
            logger.warning("No exchange rates available")
            return None
        
        # Find the exchange rate for the source currency
        for rate in rates:
            if rate.get('code', '').upper() == from_currency:
                try:
                    # Validate rate data structure
                    if transaction_type not in rate:
                        logger.error(f"Transaction type '{transaction_type}' not found in rate data")
                        return None
                    
                    rate_str = str(rate[transaction_type]).strip()
                    if not rate_str or rate_str == '-':
                        logger.warning(f"Invalid rate value for {from_currency}: {rate_str}")
                        return None
                    
                    # Parse the rate (remove commas and handle various formats)
                    cleaned_rate = rate_str.replace(',', '').replace(' ', '')
                    rate_value = float(cleaned_rate)
                    
                    if rate_value <= 0:
                        logger.warning(f"Invalid rate value for {from_currency}: {rate_value}")
                        return None
                    
                    if to_currency == "KRW":
                        # Convert foreign currency to KRW
                        result = amount * rate_value
                        logger.debug(f"Converted {amount} {from_currency} to {result} {to_currency}")
                        return result
                    else:
                        # For other conversions, would need more complex logic
                        logger.warning(f"Conversion to {to_currency} not yet supported")
                        return None
                        
                except (ValueError, TypeError) as e:
                    logger.error(f"Failed to parse rate for {from_currency}: {e}")
                    return None
        
        logger.warning(f"Currency {from_currency} not found in available rates")
        return None
