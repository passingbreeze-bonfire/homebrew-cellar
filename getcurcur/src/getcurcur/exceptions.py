"""Custom exceptions for getcurcur."""


class GetCurCurError(Exception):
    """Base exception for getcurcur package."""
    pass


class ProviderError(GetCurCurError):
    """Exception raised when a provider encounters an error."""
    pass


class NetworkError(ProviderError):
    """Exception raised when network request fails."""
    pass


class ParseError(ProviderError):
    """Exception raised when parsing exchange rate data fails."""
    pass


class TimeoutError(ProviderError):
    """Exception raised when operation times out."""
    pass


class ConfigError(GetCurCurError):
    """Exception raised for configuration errors."""
    pass


class CacheError(GetCurCurError):
    """Exception raised for cache-related errors."""
    pass