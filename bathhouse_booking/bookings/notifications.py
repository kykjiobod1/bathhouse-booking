import os
import logging
from typing import Optional
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения экземпляра бота
_bot_instance = None

def set_bot_instance(bot):
    """Установить экземпляр бота для отправки уведомлений"""
    global _bot_instance
    _bot_instance = bot
    logger.info("Bot instance set for notifications")

async def send_telegram_message(telegram_id: str, message: str) -> bool:
    """Отправить сообщение в Telegram"""
    global _bot_instance
    
    if not _bot_instance:
        logger.error("Bot instance not set for notifications")
        return False
    
    if not telegram_id:
        logger.error("No telegram_id provided")
        return False
    
    try:
        await _bot_instance.send_message(
            chat_id=telegram_id,
            text=message
        )
        logger.info(f"Message sent to telegram_id {telegram_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message to telegram_id {telegram_id}: {e}")
        return False

async def notify_admin_new_payment(booking_id: int) -> bool:
    """Уведомить администратора о новой оплате (асинхронная версия)"""
    from .models import Booking, SystemConfig
    from django.utils import timezone
    
    try:
        # Получаем Telegram ID администратора из SystemConfig
        admin_config = await sync_to_async(lambda: SystemConfig.objects.get(key="TELEGRAM_ADMIN_ID"))()
        admin_telegram_id = admin_config.value
        
        if not admin_telegram_id:
            logger.warning("TELEGRAM_ADMIN_ID not set in SystemConfig")
            return False
        
        booking = await sync_to_async(lambda: Booking.objects.get(id=booking_id))()
        
        # Конвертируем время из UTC в локальное (Asia/Jakarta)
        local_start = timezone.localtime(booking.start_datetime)
        local_end = timezone.localtime(booking.end_datetime)
        
        message = (
            f"💰 НОВАЯ ОПЛАТА!\n"
            f"Бронирование #{booking.id}\n"
            f"Клиент: {booking.client.name}\n"
            f"Телефон: {booking.client.phone or 'не указан'}\n"
            f"Telegram: @{booking.client.telegram_id or 'не указан'}\n"
            f"Баня: {booking.bathhouse.name}\n"
            f"Дата и время: {local_start.strftime('%d.%m.%Y %H:%M')} - {local_end.strftime('%H:%M')}\n"
            f"Сумма: {booking.prepayment_amount or 'не указана'} руб.\n\n"
            f"Перейдите в админку для подтверждения: /admin"
        )
        
        return await send_telegram_message(admin_telegram_id, message)
        
    except SystemConfig.DoesNotExist:
        logger.warning("TELEGRAM_ADMIN_ID not found in SystemConfig")
        return False
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
        return False

async def notify_booking_status_change(booking_id: int, old_status: str, new_status: str) -> bool:
    """Уведомить клиента об изменении статуса бронирования (асинхронная версия)"""
    from .models import Booking
    from django.utils import timezone
    
    try:
        booking = await sync_to_async(Booking.objects.get)(id=booking_id)
        
        if not booking.client.telegram_id:
            logger.warning(f"Client {booking.client.id} has no telegram_id")
            return False
        
        # Конвертируем время из UTC в локальное (Asia/Jakarta)
        local_start = timezone.localtime(booking.start_datetime)
        local_end = timezone.localtime(booking.end_datetime)
        
        status_messages = {
            'approved': f"✅ Ваше бронирование #{booking.id} подтверждено!\n"
                       f"Баня: {booking.bathhouse.name}\n"
                       f"Дата и время: {local_start.strftime('%d.%m.%Y %H:%M')} - {local_end.strftime('%H:%M')}\n"
                       f"Статус: Подтверждено\n\nЖдем вас в указанное время!",
            
            'rejected': f"❌ Ваше бронирование #{booking.id} отклонено.\n"
                       f"Баня: {booking.bathhouse.name}\n"
                       f"Дата и время: {local_start.strftime('%d.%m.%Y %H:%M')} - {local_end.strftime('%H:%M')}\n"
                       f"Причина: {booking.comment.split('Отклонено: ')[-1] if 'Отклонено:' in booking.comment else 'Не указана'}",
            
            'cancelled': f"🗑️ Ваше бронирование #{booking.id} отменено.\n"
                        f"Баня: {booking.bathhouse.name}\n"
                        f"Дата и время: {local_start.strftime('%d.%m.%Y %H:%M')} - {local_end.strftime('%H:%M')}"
        }
        
        if new_status in status_messages:
            message = status_messages[new_status]
            return await send_telegram_message(booking.client.telegram_id, message)
        else:
            logger.info(f"No notification for status change from {old_status} to {new_status}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to send booking status notification: {e}")
        return False


def send_booking_status_notification(booking_id: int, old_status: str, new_status: str) -> None:
    """Отправить уведомление об изменении статуса бронирования (синхронная версия)"""
    from .models import Booking, NotificationQueue
    from django.utils import timezone
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        if not booking.client.telegram_id:
            logger.warning(f"Client {booking.client.id} has no telegram_id")
            return
        
        # Конвертируем время из UTC в локальное (Asia/Jakarta)
        local_start = timezone.localtime(booking.start_datetime)
        local_end = timezone.localtime(booking.end_datetime)
        
        status_messages = {
            'approved': f"✅ Ваше бронирование #{booking.id} подтверждено!\n"
                       f"Баня: {booking.bathhouse.name}\n"
                       f"Дата и время: {local_start.strftime('%d.%m.%Y %H:%M')} - {local_end.strftime('%H:%M')}\n"
                       f"Статус: Подтверждено\n\nЖдем вас в указанное время!",
            
            'rejected': f"❌ Ваше бронирование #{booking.id} отклонено.\n"
                       f"Баня: {booking.bathhouse.name}\n"
                       f"Дата и время: {local_start.strftime('%d.%m.%Y %H:%M')} - {local_end.strftime('%H:%M')}\n"
                       f"Причина: {booking.comment.split('Отклонено: ')[-1] if 'Отклонено:' in booking.comment else 'Не указана'}",
            
            'cancelled': f"🗑️ Ваше бронирование #{booking.id} отменено.\n"
                        f"Баня: {booking.bathhouse.name}\n"
                        f"Дата и время: {local_start.strftime('%d.%m.%Y %H:%M')} - {local_end.strftime('%H:%M')}"
        }
        
        if new_status in status_messages:
            message = status_messages[new_status]
            # Сохраняем уведомление в базе данных для отправки ботом
            NotificationQueue.objects.create(
                telegram_id=booking.client.telegram_id,
                message=message,
                booking_id=booking_id,
                status=new_status
            )
            logger.info(f"Notification queued for booking {booking_id}: {new_status}")
        else:
            logger.info(f"No notification for status change from {old_status} to {new_status}")
            
    except Exception as e:
        logger.error(f"Failed to prepare booking status notification: {e}")