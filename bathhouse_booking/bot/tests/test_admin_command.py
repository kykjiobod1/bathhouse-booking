import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User
from bot.handlers.admin import cmd_admin
import os

class TestAdminCommand:
    """Тесты для команды /admin"""
    
    @pytest.mark.asyncio
    async def test_admin_command_no_password(self):
        """Тест команды /admin без пароля"""
        mock_message = AsyncMock(spec=Message)
        mock_message.text = "/admin"
        mock_message.from_user = User(id=123, is_bot=False, first_name="Test")
        mock_message.answer = AsyncMock()
        
        await cmd_admin(mock_message)
        
        # Проверяем, что отправлено сообщение об использовании
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Использование: /admin пароль" in call_args
    
    @pytest.mark.asyncio
    async def test_admin_command_wrong_password(self):
        """Тест команды /admin с неверным паролем"""
        mock_message = AsyncMock(spec=Message)
        mock_message.text = "/admin wrongpassword"
        mock_message.from_user = User(id=123, is_bot=False, first_name="Test")
        mock_message.answer = AsyncMock()
        
        # Устанавливаем правильный пароль в переменных окружения
        with patch.dict(os.environ, {"ADMIN_PASSWORD": "correctpassword"}):
            await cmd_admin(mock_message)
        
        # Проверяем, что отправлено сообщение о неверном пароле
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "❌ Неверный пароль." in call_args
    
    @pytest.mark.asyncio
    async def test_admin_command_correct_password(self):
        """Тест команды /admin с правильным паролем"""
        mock_message = AsyncMock(spec=Message)
        mock_message.text = "/admin correctpassword"
        mock_message.from_user = User(id=123, is_bot=False, first_name="Test")
        mock_message.answer = AsyncMock()
        
        # Мокаем SystemConfig.objects.get_or_create
        mock_config = MagicMock()
        mock_config.value = "123"
        mock_config.save = AsyncMock()
        
        with patch.dict(os.environ, {"ADMIN_PASSWORD": "correctpassword"}):
            with patch('bot.handlers.admin.sync_to_async') as mock_sync_to_async:
                # Настраиваем mock для sync_to_async - должен возвращать async функцию
                async def mock_get_or_create(*args, **kwargs):
                    return (mock_config, True)  # created=True
                
                mock_sync_to_async.return_value = mock_get_or_create
                
                await cmd_admin(mock_message)
        
        # Проверяем, что отправлено сообщение об успехе
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "✅ Вы назначены администратором!" in call_args
        assert "Ваш Telegram ID: 123" in call_args
    
    @pytest.mark.asyncio
    async def test_admin_command_update_existing(self):
        """Тест команды /admin для обновления существующего ID"""
        mock_message = AsyncMock(spec=Message)
        mock_message.text = "/admin correctpassword"
        mock_message.from_user = User(id=456, is_bot=False, first_name="Test")
        mock_message.answer = AsyncMock()
        
        # Мокаем SystemConfig.objects.get_or_create
        mock_config = MagicMock()
        mock_config.value = "123"  # Старый ID
        mock_config.save = AsyncMock()
        
        with patch.dict(os.environ, {"ADMIN_PASSWORD": "correctpassword"}):
            with patch('bot.handlers.admin.sync_to_async') as mock_sync_to_async:
                # Настраиваем mock для sync_to_async - должен возвращать async функцию
                call_count = 0
                async def mock_sync_func(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:  # get_or_create call
                        return (mock_config, False)  # created=False
                    elif call_count == 2:  # save call
                        return None
                    return None
                
                mock_sync_to_async.return_value = mock_sync_func
                
                await cmd_admin(mock_message)
        
        # Проверяем, что значение обновлено
        assert mock_config.value == "456"
        # Проверяем, что sync_to_async был вызван дважды (get_or_create и save)
        assert mock_sync_to_async.call_count == 2
        
        # Проверяем, что отправлено сообщение об успехе
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "✅ Вы назначены администратором!" in call_args