import asyncio
import logging
import os
from datetime import datetime, timedelta

# Setup Django before importing Django models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathhouse_booking.config.settings')
import django
django.setup()

# Инициализация конфигурации будет выполнена асинхронно в main()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from asgiref.sync import sync_to_async

from .routers import router
from .dependencies import setup_dependencies
from bathhouse_booking.bookings.notifications import set_bot_instance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_notification_queue(bot: Bot) -> None:
    """Обработать очередь уведомлений"""
    try:
        from bathhouse_booking.bookings.models import NotificationQueue
        from django.utils import timezone
        
        # Получаем непрочитанные уведомления (не старше 24 часов)
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        notifications = await sync_to_async(list)(
            NotificationQueue.objects.filter(
                sent_at__isnull=True,
                created_at__gte=twenty_four_hours_ago,
                attempts__lt=3  # Максимум 3 попытки
            ).order_by('created_at')[:10]  # Берем первые 10
        )
        
        for notification in notifications:
            try:
                if not notification.telegram_id or not notification.telegram_id.isdigit():
                    logger.warning(f"Invalid telegram_id: {notification.telegram_id}")
                    notification.attempts += 1
                    await sync_to_async(notification.save)()
                    continue

                chat_id = int(notification.telegram_id)
                await bot.send_message(
                    chat_id=chat_id,
                    text=notification.message
                )
                # Помечаем как отправленное
                notification.sent_at = timezone.now()
                notification.attempts += 1
                await sync_to_async(notification.save)()
                logger.info(f"Notification sent to {notification.telegram_id}")
                
                # Небольшая пауза между отправками
                await asyncio.sleep(0.5)
                
            except Exception as e:
                # Увеличиваем счетчик попыток
                notification.attempts += 1
                await sync_to_async(notification.save)()
                logger.error(f"Failed to send notification to {notification.telegram_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error processing notification queue: {e}")


async def notification_queue_worker(bot: Bot) -> None:
    """Фоновая задача для обработки очереди уведомлений"""
    while True:
        try:
            await process_notification_queue(bot)
        except Exception as e:
            logger.error(f"Error in notification queue worker: {e}")
        
        # Ждем 5 секунд перед следующей проверкой
        await asyncio.sleep(5)


async def main() -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

    # Инициализируем системную конфигурацию асинхронно
    from bathhouse_booking.bookings.config_init import initialize_system_config_async
    await initialize_system_config_async()
    
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Устанавливаем экземпляр бота для уведомлений
    set_bot_instance(bot)
    
    dp = Dispatcher()
    dp.include_router(router)
    
    await setup_dependencies(dp)
    
    # Запускаем фоновую задачу для обработки очереди уведомлений
    queue_task = asyncio.create_task(notification_queue_worker(bot))
    
    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        # Отменяем фоновую задачу при остановке бота
        queue_task.cancel()
        try:
            await queue_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())