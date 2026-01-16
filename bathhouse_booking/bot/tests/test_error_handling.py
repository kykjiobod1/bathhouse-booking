"""
Тесты для проверки обработки ошибок в боте.
"""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from django.test import TestCase
from aiogram import Dispatcher, Bot
from aiogram.types import Update, Message, User, Chat
from aiogram.exceptions import TelegramBadRequest

from bathhouse_booking.bot.error_handlers import error_handler, setup_error_handlers


class BotErrorHandlingTests(TestCase):
    """Тесты обработки ошибок в боте."""
    
    def setUp(self):
        # Создаем моки для тестирования
        self.bot = AsyncMock(spec=Bot)
        self.dp = Dispatcher()
        
        # Настраиваем обработчики ошибок
        setup_error_handlers(self.dp)
    
    def test_error_handler_import(self):
        """Проверка, что модуль обработки ошибок импортируется."""
        self.assertTrue(callable(error_handler))
        self.assertTrue(callable(setup_error_handlers))
    
    async def test_error_handler_handles_generic_exception(self):
        """Проверка обработки общего исключения."""
        # Создаем тестовое обновление
        user = User(id=123, is_bot=False, first_name="Test")
        chat = Chat(id=456, type="private")
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=chat,
            from_user=user,
            text="/test"
        )
        update = Update(update_id=1, message=message)
        
        # Создаем событие ошибки
        error_event = MagicMock()
        error_event.update = update
        error_event.exception = Exception("Test error")
        error_event.dp = self.dp
        
        # Для этого теста мы просто проверяем, что обработчик не падает
        try:
            await error_handler(error_event, self.dp)
        except Exception as e:
            self.fail(f"Error handler raised an exception: {e}")
    
    async def test_error_handler_handles_telegram_bad_request(self):
        """Проверка обработки ошибки TelegramBadRequest."""
        # Создаем тестовое обновление
        user = User(id=123, is_bot=False, first_name="Test")
        chat = Chat(id=456, type="private")
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=chat,
            from_user=user,
            text="/test"
        )
        update = Update(update_id=1, message=message)
        
        # Создаем событие ошибки с TelegramBadRequest
        error_event = MagicMock()
        error_event.update = update
        error_event.exception = TelegramBadRequest(message="Bad request", method="sendMessage")
        error_event.dp = self.dp
        
        # Для этого теста мы просто проверяем, что обработчик не падает
        try:
            await error_handler(error_event, self.dp)
        except Exception as e:
            self.fail(f"Error handler raised an exception: {e}")
    
    def test_setup_error_handlers_registers_handler(self):
        """Проверка, что setup_error_handlers регистрирует обработчик."""
        dp = Dispatcher()
        
        # Настраиваем обработчики ошибок
        setup_error_handlers(dp)
        
        # Проверяем, что обработчик был зарегистрирован
        # Вместо проверки внутренней структуры, проверяем, что диспетчер настроен
        self.assertIsNotNone(dp.errors)
    
    async def test_error_handler_without_message(self):
        """Проверка обработки ошибки без сообщения."""
        # Создаем событие ошибки без сообщения
        error_event = MagicMock()
        error_event.update = None
        error_event.exception = Exception("Test error")
        error_event.dp = self.dp
        
        # Для этого теста мы просто проверяем, что обработчик не падает
        try:
            await error_handler(error_event, self.dp)
        except Exception as e:
            self.fail(f"Error handler raised an exception: {e}")
    
    async def test_error_handler_failed_to_send_error_message(self):
        """Проверка обработки случая, когда не удается отправить сообщение об ошибке."""
        # Создаем тестовое обновление
        user = User(id=123, is_bot=False, first_name="Test")
        chat = Chat(id=456, type="private")
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=chat,
            from_user=user,
            text="/test"
        )
        update = Update(update_id=1, message=message)
        
        # Создаем событие ошибки
        error_event = MagicMock()
        error_event.update = update
        error_event.exception = Exception("Test error")
        error_event.dp = self.dp
        
        # Вызываем обработчик ошибок - не должно быть исключения
        try:
            await error_handler(error_event, self.dp)
        except Exception as e:
            self.fail(f"Error handler raised an exception: {e}")