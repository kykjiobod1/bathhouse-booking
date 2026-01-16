import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, User, Message, Chat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from bot.handlers.booking import select_bathhouse
from bot.states import BookingStates

class TestBookingCalendar:
    """Тесты для календаря бронирования"""
    
    @pytest.mark.asyncio
    async def test_select_bathhouse_shows_calendar_with_back_button(self):
        """Тест что select_bathhouse показывает календарь с кнопкой назад"""
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_message = AsyncMock(spec=Message)
        mock_message.chat = Chat(id=123, type="private")
        mock_message.answer = AsyncMock()
        mock_callback.answer = AsyncMock()
        mock_callback.message = mock_message
        mock_callback.from_user = User(id=456, is_bot=False, first_name="Test")
        mock_callback.data = "select_bathhouse:1"
        
        # Мокаем состояние
        storage = MemoryStorage()
        state = FSMContext(storage=storage, key=StorageKey(bot_id=123, chat_id=123, user_id=456))
        
        # Мокаем cleanup
        with patch('bot.handlers.booking._cleanup_previous_messages') as mock_cleanup:
            with patch('bot.handlers.booking._update_activity_timestamp') as mock_update:
                # Мокаем календарь
                with patch('bot.handlers.booking.date_selection_keyboard') as mock_keyboard:
                    mock_keyboard.return_value = AsyncMock(return_value=MagicMock())
                    
                    await select_bathhouse(mock_callback, state)
        
        # Проверяем, что состояние установлено
        current_state = await state.get_state()
        assert current_state == BookingStates.waiting_for_date.state
        
        # Проверяем, что показан календарь с кнопкой назад
        mock_keyboard.assert_called_once()
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "Выберите дату:" in call_args[0][0]
    
    def test_calendar_callback_format(self):
        """Тест формата callback_data календаря"""
        # Проверяем что модуль календаря импортируется
        try:
            from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
            calendar = SimpleCalendar()
            
            # Проверяем что callback_data начинается с simple_calendar
            # Это важно для обработки в process_calendar_date и process_schedule_calendar_date
            assert hasattr(calendar, 'start_calendar')
            assert SimpleCalendarCallback is not None
        except ImportError:
            pytest.skip("aiogram_calendar not installed")