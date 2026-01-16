import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, User, Message, Chat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from bot.handlers.booking import view_schedule
from bot.states import BookingStates

class TestScheduleCalendar:
    """Тесты для календаря расписания"""
    
    @pytest.mark.asyncio
    async def test_view_schedule_shows_calendar(self):
        """Тест что view_schedule показывает календарь"""
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_message = AsyncMock(spec=Message)
        mock_message.chat = Chat(id=123, type="private")
        mock_message.answer = AsyncMock()
        mock_callback.answer = AsyncMock()
        mock_callback.message = mock_message
        mock_callback.from_user = User(id=456, is_bot=False, first_name="Test")
        
        # Мокаем состояние
        storage = MemoryStorage()
        state = FSMContext(storage=storage, key=StorageKey(bot_id=123, chat_id=123, user_id=456))
        
        # Мокаем sync_to_async для получения бань
        with patch('bot.handlers.booking.sync_to_async') as mock_sync:
            mock_bathhouse = MagicMock(name="Баня 1", is_active=True)
            mock_bathhouse.id = 1
            mock_bathhouses = [mock_bathhouse]
            # sync_to_async должен возвращать async функцию
            async def mock_async_func(*args, **kwargs):
                return mock_bathhouses
            mock_sync.return_value = mock_async_func
            
            # Мокаем календарь - патчим модуль в sys.modules
            import sys
            mock_calendar = AsyncMock(return_value=MagicMock())
            mock_module = MagicMock()
            mock_module.get_calendar_keyboard = mock_calendar
            
            with patch.dict(sys.modules, {'bathhouse_booking.bot.calendar_utils': mock_module}):
                await view_schedule(mock_callback, state)
        
        # Проверяем, что состояние установлено
        current_state = await state.get_state()
        assert current_state == BookingStates.waiting_for_schedule_date.state
        
        # Проверяем, что сообщение отправлено (календарь или нет бань)
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        # Проверяем либо сообщение о наличии бань, либо об их отсутствии
        assert "Выберите дату для просмотра расписания" in call_args or "нет доступных бань" in call_args
    
    @pytest.mark.asyncio
    async def test_view_schedule_no_bathhouses(self):
        """Тест view_schedule когда нет доступных бань"""
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_message = AsyncMock(spec=Message)
        mock_message.chat = Chat(id=123, type="private")
        mock_message.answer = AsyncMock()
        mock_callback.answer = AsyncMock()
        mock_callback.message = mock_message
        mock_callback.from_user = User(id=456, is_bot=False, first_name="Test")
        
        storage = MemoryStorage()
        state = FSMContext(storage=storage, key=StorageKey(bot_id=123, chat_id=123, user_id=456))
        
        # Мокаем пустой список бань
        with patch('bot.handlers.booking.sync_to_async') as mock_sync:
            # sync_to_async должен возвращать async функцию
            async def mock_async_func(*args, **kwargs):
                return []
            mock_sync.return_value = mock_async_func
            
            await view_schedule(mock_callback, state)
        
        # Проверяем сообщение об отсутствии бань
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "К сожалению, сейчас нет доступных бань." in call_args
        
        # Проверяем, что состояние не установлено
        current_state = await state.get_state()
        assert current_state is None