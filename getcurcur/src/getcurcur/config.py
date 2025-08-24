"""Configuration management for getcurcur."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for getcurcur."""
    
    DEFAULT_CONFIG = {
        "default_provider": "korea.hana",
        "cache": {
            "enabled": True,
            "ttl_minutes": 30
        },
        "browser": {
            "headless": True,
            "timeout": 30000
        },
        "output": {
            "default_format": "table",
            "default_currency": None
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or Path.home() / ".getcurcur" / "config.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default.
        
        Attempts to load configuration from the specified config file path.
        If the file doesn't exist, creates a new one with default values.
        If loading fails due to invalid JSON or other errors, falls back to defaults.
        
        Returns:
            Dict containing the loaded or default configuration
            
        Note:
            User configuration is merged with defaults to ensure all required keys exist.
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # Merge with defaults
                config = self.DEFAULT_CONFIG.copy()
                self._deep_merge(config, user_config)
                return config
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _deep_merge(self, base: Dict, override: Dict):
        """
        Deep merge override dictionary into base dictionary.
        
        Recursively merges nested dictionaries, preserving the structure
        while allowing override values to take precedence.
        
        Args:
            base: Base dictionary to merge into (modified in-place)
            override: Dictionary with override values
            
        Example:
            base = {"a": {"b": 1, "c": 2}}
            override = {"a": {"b": 10}}
            After merge: {"a": {"b": 10, "c": 2}}
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _save_config(self, config: Dict[str, Any]):
        """
        Save configuration to file.
        
        Writes the configuration dictionary to the config file path as JSON.
        Creates parent directories if they don't exist. Logs errors but doesn't raise.
        
        Args:
            config: Configuration dictionary to save
            
        Note:
            Uses UTF-8 encoding and formatted JSON (2-space indent) for readability.
        """
        from ..exceptions import ConfigError
        
        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"Configuration saved to {self.config_path}")
        except (OSError, json.JSONEncodeError) as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")
            # Don't raise to avoid breaking the application
        except Exception as e:
            # Log unexpected errors but don't crash
            logger.error(f"Unexpected error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., "cache.enabled")
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save to file
        self._save_config(self.config)
    
    def reset(self):
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self._save_config(self.config)


# Global config instance
_config = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config