"""Tests for CLI commands."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
import json

from getcurcur.main import app

runner = CliRunner()


class TestShowCommand:
    """Test 'show' command."""
    
    @patch('getcurcur.main.get_browser_manager')
    @patch('getcurcur.main.get_provider')
    def test_show_default(self, mock_get_provider, mock_get_bm):
        """Test show command with default options."""
        # Setup mock browser manager
        mock_context = MagicMock()
        mock_bm = MagicMock()
        mock_bm.browser_context.return_value.__enter__.return_value = mock_context
        mock_bm.browser_context.return_value.__exit__.return_value = None
        mock_get_bm.return_value = mock_bm
        
        # Setup mock provider
        mock_provider = MagicMock()
        mock_provider.get_provider_name.return_value = "Test Bank"
        mock_provider.get_rates.return_value = [
            {
                "currency": "US Dollar",
                "code": "USD",
                "cash_buy": "1,300.00",
                "cash_sell": "1,350.00",
                "provider": "Test Bank",
                "country": "KR"
            }
        ]
        mock_get_provider.return_value = mock_provider
        
        result = runner.invoke(app, ["show"])
        assert result.exit_code == 0
        assert "USD" in result.stdout
        assert "1,300.00" in result.stdout

    @patch('getcurcur.main.get_browser_manager')
    @patch('getcurcur.main.get_provider')
    def test_show_json_format(self, mock_get_provider, mock_get_bm):
        """Test show command with JSON output."""
        # Setup mock browser manager
        mock_context = MagicMock()
        mock_bm = MagicMock()
        mock_bm.browser_context.return_value.__enter__.return_value = mock_context
        mock_bm.browser_context.return_value.__exit__.return_value = None
        mock_get_bm.return_value = mock_bm
        
        mock_provider = MagicMock()
        mock_provider.get_provider_name.return_value = "Test Bank"
        mock_provider.get_rates.return_value = [
            {
                "currency": "US Dollar",
                "code": "USD",
                "cash_buy": "1,300.00",
                "cash_sell": "1,350.00"
            }
        ]
        mock_get_provider.return_value = mock_provider
        
        result = runner.invoke(app, ["show", "-f", "json"])
        assert result.exit_code == 0
        
        # Should be valid JSON
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["code"] == "USD"

    @patch('getcurcur.main.get_browser_manager')
    @patch('getcurcur.main.get_provider')
    def test_show_currency_filter(self, mock_get_provider, mock_get_bm):
        """Test show command with currency filter."""
        # Setup mock browser manager
        mock_context = MagicMock()
        mock_bm = MagicMock()
        mock_bm.browser_context.return_value.__enter__.return_value = mock_context
        mock_bm.browser_context.return_value.__exit__.return_value = None
        mock_get_bm.return_value = mock_bm
        
        mock_provider = MagicMock()
        mock_provider.get_provider_name.return_value = "Test Bank"
        mock_provider.get_rates.return_value = [
            {"code": "USD", "cash_buy": "1,300.00", "cash_sell": "1,350.00", "currency": "US Dollar"},
            {"code": "EUR", "cash_buy": "1,400.00", "cash_sell": "1,450.00", "currency": "Euro"}
        ]
        mock_get_provider.return_value = mock_provider
        
        result = runner.invoke(app, ["show", "-c", "USD"])
        assert result.exit_code == 0
        assert "USD" in result.stdout
        assert "EUR" not in result.stdout
    
    def test_show_invalid_provider(self):
        """Test show command with invalid provider."""
        result = runner.invoke(app, ["show", "-b", "invalid_bank"])
        assert result.exit_code == 1
        assert "Error" in result.stdout


class TestConvertCommand:
    """Test 'convert' command."""
    
    @patch('getcurcur.main.get_browser_manager')
    @patch('getcurcur.main.get_provider')
    def test_convert_success(self, mock_get_provider, mock_get_bm):
        """Test successful currency conversion."""
        # Setup mock browser manager
        mock_context = MagicMock()
        mock_bm = MagicMock()
        mock_bm.browser_context.return_value.__enter__.return_value = mock_context
        mock_bm.browser_context.return_value.__exit__.return_value = None
        mock_get_bm.return_value = mock_bm
        
        mock_provider = MagicMock()
        mock_provider.get_provider_name.return_value = "Test Bank"
        mock_provider.convert_amount.return_value = 130000.0
        mock_get_provider.return_value = mock_provider
        
        result = runner.invoke(app, ["convert", "100", "USD"])
        assert result.exit_code == 0
        assert "100.00 USD = 130,000.00 KRW" in result.stdout

    @patch('getcurcur.main.get_browser_manager')
    @patch('getcurcur.main.get_provider')
    def test_convert_with_options(self, mock_get_provider, mock_get_bm):
        """Test conversion with custom options."""
        mock_context = MagicMock()
        mock_bm = MagicMock()
        mock_bm.browser_context.return_value.__enter__.return_value = mock_context
        mock_get_bm.return_value = mock_bm

        mock_provider = MagicMock()
        mock_provider.get_provider_name.return_value = "Test Bank"
        mock_provider.convert_amount.return_value = 135000.0
        mock_get_provider.return_value = mock_provider
        
        result = runner.invoke(app, ["convert", "100", "USD", "--type", "sell"])
        assert result.exit_code == 0
        mock_provider.convert_amount.assert_called_with(
          amount=100.0, from_currency="USD", context=mock_context, to_currency="KRW", transaction_type="cash_sell"
        )


class TestListProvidersCommand:
    """Test 'list-providers' command."""
    
    def test_list_providers(self):
        """Test listing available providers."""
        result = runner.invoke(app, ["list-providers"])
        assert result.exit_code == 0
        assert "korea.hana" in result.stdout
        assert "korea.woori" in result.stdout


class TestClearCacheCommand:
    """Test 'clear-cache' command."""
    
    @patch('getcurcur.main.shutil.rmtree')
    @patch('getcurcur.main.Path')
    def test_clear_cache_success(self, mock_path_class, mock_rmtree):
        """Test successful cache clearing."""
        # Setup path mocks
        mock_cache_dir = MagicMock()
        mock_cache_dir.exists.return_value = True
        mock_cache_dir.is_dir.return_value = True
        
        # Mock Path.home() / ".getcurcur" / "cache"
        mock_path_class.home.return_value.__truediv__.return_value.__truediv__.return_value = mock_cache_dir
        
        result = runner.invoke(app, ["clear-cache"])
        assert result.exit_code == 0
        assert "Cache cleared successfully" in result.stdout
        mock_rmtree.assert_called_once_with(mock_cache_dir)
    
    @patch('getcurcur.main.Path')
    def test_clear_cache_no_cache(self, mock_path_class):
        """Test clearing cache when no cache exists."""
        # Setup path mocks
        mock_cache_dir = MagicMock()
        mock_cache_dir.exists.return_value = False
        
        # Mock Path.home() / ".getcurcur" / "cache"
        mock_path_class.home.return_value.__truediv__.return_value.__truediv__.return_value = mock_cache_dir
        
        result = runner.invoke(app, ["clear-cache"])
        assert result.exit_code == 0
        assert "No cache to clear" in result.stdout


class TestVersionOption:
    """Test version option."""
    
    def test_version(self):
        """Test --version option."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "getcurcur version" in result.stdout
