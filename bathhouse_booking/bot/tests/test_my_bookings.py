import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, User, Message, Chat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from bot.handlers.my_bookings import (
    show_my_bookings, 
    view_booking_detail, 
    cancel_user_booking,
    create_booking_detail_keyboard,
    create_bookings_keyboard
)
from bathhouse_booking.bookings.models import Booking, Client

class TestMyBookings:
    """Тесты для функционала 'мои бронирования'"""
    
    def test_create_bookings_keyboard_has_back_button(self):
        """Тест что клавиатура бронирований имеет кнопку назад"""
        bookings = []
        keyboard = create_bookings_keyboard(bookings)
        
        # Проверяем что есть кнопка "назад"
        assert len(keyboard.inline_keyboard) == 1
        assert keyboard.inline_keyboard[0][0].text == "⬅️ Назад"
        assert keyboard.inline_keyboard[0][0].callback_data == "back_to_main"
    
    def test_create_booking_detail_keyboard_has_home_button(self):
        """Тест что клавиатура деталей бронирования имеет кнопку 'на главную'"""
        booking_id = 1
        keyboard = create_booking_detail_keyboard(booking_id, can_cancel=True)
        
        # Проверяем что есть кнопки: отмена, назад к списку, на главную
        buttons = keyboard.inline_keyboard
        assert len(buttons) == 3
        
        # Проверяем кнопки
        assert buttons[0][0].text == "❌ Отменить бронирование"
        assert buttons[0][0].callback_data == "cancel_booking:1"
        
        assert buttons[1][0].text == "⬅️ Назад к списку"
        assert buttons[1][0].callback_data == "back_to_my_bookings"
        
        assert buttons[2][0].text == "🏠 На главную"
        assert buttons[2][0].callback_data == "back_to_main"
    
    @pytest.mark.asyncio
    async def test_show_my_bookings_no_bookings(self):
        """Тест показа бронирований когда их нет"""
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_message = AsyncMock(spec=Message)
        mock_message.chat = Chat(id=123, type="private")
        mock_message.edit_text = AsyncMock()
        mock_callback.message = mock_message
        mock_callback.from_user = User(id=456, is_bot=False, first_name="Test")
        
        # Мокаем состояние
        storage = MemoryStorage()
        state = FSMContext(storage=storage, key=StorageKey(bot_id=123, chat_id=123, user_id=456))
        
        # Мокаем get_user_bookings напрямую, так как это async функция
        with patch('bot.handlers.my_bookings.get_user_bookings') as mock_get:
            # get_user_bookings это async функция
            mock_get.return_value = []
            
            await show_my_bookings(mock_callback, state)
            
            # Проверяем сообщение об отсутствии бронирований
            mock_message.edit_text.assert_called_once()
            call_args = mock_message.edit_text.call_args[0][0]
            assert "У вас нет активных бронирований" in call_args
    
    @pytest.mark.asyncio 
    async def test_cancel_booking_success(self):
        """Тест успешной отмены бронирования"""
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_message = AsyncMock(spec=Message)
        mock_message.chat = Chat(id=123, type="private")
        mock_message.edit_text = AsyncMock()
        mock_callback.message = mock_message
        mock_callback.from_user = User(id=456, is_bot=False, first_name="Test")
        mock_callback.data = "cancel_booking:1"
        
        # Мокаем состояние
        storage = MemoryStorage()
        state = FSMContext(storage=storage, key=StorageKey(bot_id=123, chat_id=123, user_id=456))
        
        # Мокаем клиента и бронирование
        mock_client = MagicMock()
        mock_client.id = 1
        
        mock_booking = MagicMock()
        mock_booking.id = 1
        mock_booking.client = mock_client
        
        # Мокаем sync_to_async для разных вызовов
        with patch('bot.handlers.my_bookings.sync_to_async') as mock_sync:
            # Создаем async функции для моков
            call_count = 0
            async def async_mock(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:  # Client.objects.get
                    return mock_client
                elif call_count == 2:  # Booking.objects.select_related().get
                    return mock_booking
                elif call_count == 3:  # cancel_booking
                    return None
                return MagicMock()
            
            mock_sync.return_value = async_mock
            
            await cancel_user_booking(mock_callback, state)
        
        # Проверяем сообщение об успешной отмене
        mock_message.edit_text.assert_called_once()
        call_args = mock_message.edit_text.call_args[0][0]
        assert "Бронирование успешно отменено" in call_args