import os
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock


class TestBotLaunch:
    def test_main_function_exists(self):
        from bot.main import main
        assert callable(main)
    
    def test_main_requires_token(self):
        from bot.main import main
        
        if "TELEGRAM_BOT_TOKEN" in os.environ:
            del os.environ["TELEGRAM_BOT_TOKEN"]
        
        with patch('bot.main.Bot') as mock_bot:
            with patch('bot.main.Dispatcher') as mock_dp:
                mock_dp_instance = AsyncMock()
                mock_dp.return_value = mock_dp_instance
                
                try:
                    asyncio.run(main())
                    assert False, "Should have raised ValueError"
                except ValueError as e:
                    assert "TELEGRAM_BOT_TOKEN" in str(e)
    
    def test_main_with_token(self):
        os.environ["TELEGRAM_BOT_TOKEN"] = "test_token:123456"
        
        from bot.main import main
        
        with patch('bot.main.Bot') as mock_bot:
            with patch('bot.main.Dispatcher') as mock_dp:
                with patch('bot.main.setup_dependencies') as mock_setup:
                    mock_dp_instance = AsyncMock()
                    mock_dp.return_value = mock_dp_instance
                    mock_bot_instance = AsyncMock()
                    mock_bot.return_value = mock_bot_instance
                    
                    mock_dp_instance.start_polling = AsyncMock(return_value=None)
                    
                    try:
                        asyncio.run(main())
                    except Exception as e:
                        if not isinstance(e, (RuntimeError, AttributeError)):
                            raise
                    
                    mock_bot.assert_called_once()
                    mock_dp.assert_called_once()
                    mock_setup.assert_called_once_with(mock_dp_instance)
                    mock_dp_instance.start_polling.assert_called_once_with(mock_bot_instance)