import logging
from typing import Any

from aiogram import Dispatcher
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
)
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)


async def error_handler(event: ErrorEvent) -> None:
    """
    Глобальный обработчик ошибок для бота.
    Логирует ошибки и отправляет пользователю безопасное сообщение.
    """
    exception = event.exception
    
    # Логируем ошибку
    logger.error(
        f"Error in bot handler: {exception}",
        exc_info=exception,
        extra={
            "update": event.update.model_dump() if event.update else None,
            "user_id": event.update.message.from_user.id if event.update and event.update.message else None,
        }
    )
    
    # Обработка специфических ошибок Telegram
    if isinstance(exception, TelegramRetryAfter):
        logger.warning(f"Rate limit exceeded: retry after {exception.retry_after} seconds")
        return
    
    if isinstance(exception, TelegramForbiddenError):
        logger.warning(f"Bot was blocked by user: {exception}")
        return
    
    if isinstance(exception, TelegramUnauthorizedError):
        logger.error(f"Bot token is invalid: {exception}")
        return
    
    if isinstance(exception, TelegramNetworkError):
        logger.error(f"Network error: {exception}")
        return
    
    if isinstance(exception, TelegramBadRequest):
        logger.error(f"Bad request to Telegram API: {exception}")
        return
    
    # Для других ошибок пытаемся отправить пользователю сообщение
    try:
        if event.update and event.update.message:
            await event.update.message.answer(
                "⚠️ Произошла ошибка при обработке вашего запроса. "
                "Попробуйте позже или обратитесь к администратору."
            )
    except Exception as e:
        logger.error(f"Failed to send error message to user: {e}")


def setup_error_handlers(dp: Dispatcher) -> None:
    """Настроить обработчики ошибок для диспетчера."""
    dp.errors.register(error_handler)
    logger.info("Error handlers setup complete")