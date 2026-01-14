"""
Middleware для проверки таймаута сессий бронирования.
"""
import time
import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message

from bathhouse_booking.bookings.config_init import get_config_int_async

logger = logging.getLogger(__name__)


class SessionTimeoutMiddleware(BaseMiddleware):
    """Middleware для проверки таймаута сессий бронирования"""
    
    async def __call__(self, handler, event, data):
        # Получаем FSM контекст
        state = data.get("state")
        
        if not state:
            return await handler(event, data)
        
        # Проверяем, есть ли состояние
        current_state = await state.get_state()
        if not current_state:
            return await handler(event, data)
        
        # Получаем данные состояния
        state_data = await state.get_data()
        
        # Проверяем timestamp последней активности
        last_activity = state_data.get("last_activity")
        if last_activity:
            timeout_minutes = await get_config_int_async("BOOKING_SESSION_TIMEOUT_MINUTES", 30)
            timeout_seconds = timeout_minutes * 60
            
            if time.time() - last_activity > timeout_seconds:
                # Сессия истекла, очищаем состояние
                event_chat = data.get('event_chat')
                if event_chat and hasattr(event_chat, 'id'):
                    logger.info(f"Session timeout for chat {event_chat.id}")
                await state.clear()
                
                # Отправляем сообщение об истечении сессии
                try:
                    if isinstance(event, CallbackQuery) and event.message:
                        await event.message.answer(
                            "Сессия бронирования истекла из-за неактивности. "
                            "Пожалуйста, начните процесс бронирования заново."
                        )
                    elif isinstance(event, Message):
                        await event.answer(
                            "Сессия бронирования истекла из-за неактивности. "
                            "Пожалуйста, начните процесс бронирования заново."
                        )
                except Exception as e:
                    logger.error(f"Failed to send timeout message: {e}")
                
                return
        
        # Обновляем timestamp последней активности
        await state.update_data(last_activity=time.time())
        
        return await handler(event, data)