from django.core.exceptions import ValidationError
from django.db import DatabaseError
from .models import Booking, SystemConfig
from django.utils import timezone
from datetime import datetime, time, timedelta
from typing import List, Tuple
import logging
import pytz

logger = logging.getLogger(__name__)

# Часовой пояс бани (GMT+7)
BATHHOUSE_TIMEZONE = pytz.timezone('Asia/Jakarta')  # GMT+7

def check_booking_limit(client):
    """
    Проверить лимит активных бронирований клиента.
    
    Args:
        client: Клиент
        
    Raises:
        ValidationError: Если превышен лимит активных бронирований
    """
    from .config_init import get_config_int
    
    max_active_bookings = get_config_int("MAX_ACTIVE_BOOKINGS_PER_CLIENT", 3)
    
    # Считаем активные бронирования клиента
    active_bookings_count = Booking.objects.filter(  # type: ignore
        client=client,
        status__in=['pending', 'payment_reported', 'approved']
    ).count()
    
    if active_bookings_count >= max_active_bookings:
        raise ValidationError(
            f"У вас уже есть {active_bookings_count} активных бронирований. "
            f"Максимально допустимое количество: {max_active_bookings}. "
            "Пожалуйста, дождитесь обработки текущих бронирований или отмените некоторые из них."
        )


def create_booking_request(client, bathhouse, start, end, comment=None):
    """
    Создать запрос на бронирование.
    
    Args:
        client: Клиент
        bathhouse: Баня
        start: Начало бронирования
        end: Конец бронирования
        comment: Комментарий (опционально)
    
    Returns:
        Созданное бронирование
        
    Raises:
        ValidationError: Если данные невалидны или превышен лимит бронирований
        DatabaseError: Если произошла ошибка базы данных
    """
    try:
        # Проверяем лимит активных бронирований
        check_booking_limit(client)
        
        booking = Booking(
            client=client,
            bathhouse=bathhouse,
            start_datetime=start,
            end_datetime=end,
            status="pending",
            comment=comment or ""
        )

        booking.full_clean()
        booking.save()
        
        logger.info(
            f"Booking request created: ID={booking.id}, "
            f"Client={client.id}, Bathhouse={bathhouse.id}, "
            f"Start={start}, End={end}"
        )
        
        return booking
        
    except ValidationError as e:
        logger.warning(
            f"Validation error creating booking: {e}, "
            f"Client={client.id}, Bathhouse={bathhouse.id}"
        )
        raise
    except DatabaseError as e:
        logger.error(
            f"Database error creating booking: {e}, "
            f"Client={client.id}, Bathhouse={bathhouse.id}"
        )
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error creating booking: {e}, "
            f"Client={client.id}, Bathhouse={bathhouse.id}"
        )
        raise

def report_payment(booking_id):
    """
    Отметить бронирование как оплаченное.
    
    Args:
        booking_id: ID бронирования
        
    Returns:
        None
        
    Raises:
        ValidationError: Если бронирование не найдено или данные невалидны
        DatabaseError: Если произошла ошибка базы данных
    """
    try:
        booking = Booking.objects.get(id=booking_id)  # type: ignore
    except Booking.DoesNotExist:  # type: ignore
        logger.warning(f"Booking not found for payment report: ID={booking_id}")
        raise ValidationError(f"Бронирование с ID {booking_id} не найдено")

    old_status = booking.status
    booking.status = "payment_reported"
    
    try:
        booking.full_clean()
        booking.save()
        
        logger.info(
            f"Payment reported: Booking ID={booking_id}, "
            f"Old status={old_status}, New status={booking.status}"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error reporting payment for booking {booking_id}: {e}")
        raise
    except DatabaseError as e:
        logger.error(f"Database error reporting payment for booking {booking_id}: {e}")
        raise
    
    # Отправляем уведомление администратору
    try:
        from .notifications import notify_admin_new_payment
        import asyncio
        
        # Запускаем асинхронную задачу для отправки уведомления
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(notify_admin_new_payment(booking_id))
        loop.close()
        
    except Exception as e:
        logger.error(f"Failed to send admin notification for booking {booking_id}: {e}")

def approve_booking(booking_id):
    """
    Подтвердить бронирование.
    
    Args:
        booking_id: ID бронирования
        
    Returns:
        None
        
    Raises:
        ValidationError: Если бронирование не найдено, данные невалидны или есть пересечение
        DatabaseError: Если произошла ошибка базы данных
    """
    try:
        booking = Booking.objects.get(id=booking_id)  # type: ignore
    except Booking.DoesNotExist:  # type: ignore
        logger.warning(f"Booking not found for approval: ID={booking_id}")
        raise ValidationError(f"Бронирование с ID {booking_id} не найдено")

    old_status = booking.status
    booking.status = "approved"
    
    try:
        booking.full_clean()
        booking.save()
        
        logger.info(
            f"Booking approved: ID={booking_id}, "
            f"Old status={old_status}, New status={booking.status}"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error approving booking {booking_id}: {e}")
        raise
    except DatabaseError as e:
        logger.error(f"Database error approving booking {booking_id}: {e}")
        raise
    
    # Отправляем уведомление
    try:
        from .notifications import send_booking_status_notification
        # Используем простой синхронный вызов
        send_booking_status_notification(booking_id, old_status, "approved")
    except Exception as e:
        logger.error(f"Failed to send approval notification for booking {booking_id}: {e}")

def reject_booking(booking_id, reason=None):
    """
    Отклонить бронирование.
    
    Args:
        booking_id: ID бронирования
        reason: Причина отклонения (опционально)
        
    Returns:
        None
        
    Raises:
        ValidationError: Если бронирование не найдено или данные невалидны
        DatabaseError: Если произошла ошибка базы данных
    """
    try:
        booking = Booking.objects.get(id=booking_id)  # type: ignore
    except Booking.DoesNotExist:  # type: ignore
        logger.warning(f"Booking not found for rejection: ID={booking_id}")
        raise ValidationError(f"Бронирование с ID {booking_id} не найдено")

    old_status = booking.status
    booking.status = "rejected"
    if reason:
        booking.comment = f"{booking.comment}\nОтклонено: {reason}" if booking.comment else f"Отклонено: {reason}"
    
    try:
        booking.full_clean()
        booking.save()
        
        logger.info(
            f"Booking rejected: ID={booking_id}, "
            f"Old status={old_status}, New status={booking.status}, "
            f"Reason={reason or 'not specified'}"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error rejecting booking {booking_id}: {e}")
        raise
    except DatabaseError as e:
        logger.error(f"Database error rejecting booking {booking_id}: {e}")
        raise
    
    # Отправляем уведомление
    try:
        from .notifications import send_booking_status_notification
        send_booking_status_notification(booking_id, old_status, "rejected")
    except Exception as e:
        logger.error(f"Failed to send rejection notification for booking {booking_id}: {e}")


def cancel_booking(booking_id):
    """
    Отменить бронирование (клиентом).
    
    Args:
        booking_id: ID бронирования
        
    Returns:
        None
        
    Raises:
        ValidationError: Если бронирование не найдено, нельзя отменить или данные невалидны
        DatabaseError: Если произошла ошибка базы данных
    """
    try:
        booking = Booking.objects.get(id=booking_id)  # type: ignore
    except Booking.DoesNotExist:  # type: ignore
        logger.warning(f"Booking not found for cancellation: ID={booking_id}")
        raise ValidationError(f"Бронирование с ID {booking_id} не найдено")
    
    # Проверяем, можно ли отменить бронирование
    if booking.status not in ['pending', 'payment_reported']:
        logger.warning(
            f"Cannot cancel booking {booking_id}: "
            f"Invalid status {booking.status}"
        )
        raise ValidationError(f"Нельзя отменить бронирование со статусом {booking.status}")
    
    old_status = booking.status
    booking.status = "cancelled"
    
    try:
        booking.full_clean()
        booking.save()
        
        logger.info(
            f"Booking cancelled: ID={booking_id}, "
            f"Old status={old_status}, New status={booking.status}"
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error cancelling booking {booking_id}: {e}")
        raise
    except DatabaseError as e:
        logger.error(f"Database error cancelling booking {booking_id}: {e}")
        raise
    
    # Отправляем уведомление
    try:
        from .notifications import send_booking_status_notification
        send_booking_status_notification(booking_id, old_status, "cancelled")
    except Exception as e:
        logger.error(f"Failed to send cancellation notification for booking {booking_id}: {e}")


def get_available_slots(bathhouse, date) -> List[Tuple[datetime, datetime]]:
    """
    Получить доступные слоты для бронирования.
    
    Args:
        bathhouse: Объект бани
        date: Дата для поиска слотов
        
    Returns:
        Список доступных слотов (начало, конец) в часовом поясе бани
        
    Raises:
        DatabaseError: Если произошла ошибка базы данных
    """
    try:
        # Получаем настройки из конфига
        from .config_init import get_config_int
        
        open_hour = get_config_int("OPEN_HOUR", 9)
        close_hour = get_config_int("CLOSE_HOUR", 22)
        slot_step_minutes = get_config_int("SLOT_STEP_MINUTES", 30)
        min_booking_minutes = get_config_int("MIN_BOOKING_MINUTES", 120)
        
        # Создаем datetime объекты в часовом поясе бани
        start_of_day_local = BATHHOUSE_TIMEZONE.localize(datetime.combine(date, time(0, 0)))
        end_of_day_local = BATHHOUSE_TIMEZONE.localize(datetime.combine(date, time(23, 59, 59)))
        
        # Конвертируем в UTC для сравнения с данными в базе
        start_of_day_utc = start_of_day_local.astimezone(pytz.UTC)
        end_of_day_utc = end_of_day_local.astimezone(pytz.UTC)
        
        approved_bookings = list(Booking.objects.filter(  # type: ignore
            bathhouse=bathhouse,
            status="approved",
            start_datetime__lt=end_of_day_utc,
            end_datetime__gt=start_of_day_utc
        ))
        
        # Генерируем все возможные слоты в часовом поясе бани
        slots = []
        current_time_local = BATHHOUSE_TIMEZONE.localize(datetime.combine(date, time(open_hour, 0)))
        end_time_local = BATHHOUSE_TIMEZONE.localize(datetime.combine(date, time(close_hour, 0)))
        
        while current_time_local < end_time_local:
            slot_start_local = current_time_local
            slot_end_local = slot_start_local + timedelta(minutes=min_booking_minutes)
            
            if slot_end_local <= end_time_local:
                # Конвертируем в UTC для сравнения с бронированиями
                slot_start_utc = slot_start_local.astimezone(pytz.UTC)
                slot_end_utc = slot_end_local.astimezone(pytz.UTC)
                
                # Проверяем пересечение с approved бронированиями
                overlaps = False
                for booking in approved_bookings:
                    if not (slot_end_utc <= booking.start_datetime or slot_start_utc >= booking.end_datetime):
                        overlaps = True
                        break
                
                if not overlaps:
                    slots.append((slot_start_local, slot_end_local))
            
            current_time_local += timedelta(minutes=slot_step_minutes)
        
        logger.debug(
            f"Available slots found: Bathhouse={bathhouse.id}, "
            f"Date={date}, Slots count={len(slots)}"
        )
        
        return slots
        
    except DatabaseError as e:
        logger.error(f"Database error getting available slots for bathhouse {bathhouse.id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting available slots for bathhouse {bathhouse.id}: {e}")
        raise


def get_free_intervals(bathhouse, date) -> List[Tuple[datetime, datetime]]:
    """
    Calculate free intervals based on approved bookings and working hours.
    
    Args:
        bathhouse: Bathhouse object
        date: Date object
    
    Returns:
        List of (start_datetime, end_datetime) tuples for free intervals (in bathhouse timezone)
    """
    # Получаем настройки из конфига
    from .config_init import get_config_int
    
    open_hour = get_config_int("OPEN_HOUR", 9)
    close_hour = get_config_int("CLOSE_HOUR", 22)
    
    # Создаем datetime объекты в часовом поясе бани
    start_of_day_local = BATHHOUSE_TIMEZONE.localize(datetime.combine(date, time(0, 0)))
    end_of_day_local = BATHHOUSE_TIMEZONE.localize(datetime.combine(date, time(23, 59, 59)))
    
    # Конвертируем в UTC для сравнения с данными в базе
    start_of_day_utc = start_of_day_local.astimezone(pytz.UTC)
    end_of_day_utc = end_of_day_local.astimezone(pytz.UTC)
    
    approved_bookings = list(Booking.objects.filter(  # type: ignore
        bathhouse=bathhouse,
        status="approved",
        start_datetime__lt=end_of_day_utc,
        end_datetime__gt=start_of_day_utc
    ))
    
    if not approved_bookings:
        # Whole day is free
        workday_start = BATHHOUSE_TIMEZONE.localize(datetime.combine(date, time(open_hour, 0)))
        workday_end = BATHHOUSE_TIMEZONE.localize(datetime.combine(date, time(close_hour, 0)))
        return [(workday_start, workday_end)]
    
    # Sort bookings by start time
    sorted_bookings = sorted(approved_bookings, key=lambda x: x.start_datetime)
    
    # Create workday boundaries in bathhouse timezone
    workday_start = BATHHOUSE_TIMEZONE.localize(datetime.combine(date, time(open_hour, 0)))
    workday_end = BATHHOUSE_TIMEZONE.localize(datetime.combine(date, time(close_hour, 0)))
    
    free_intervals = []
    current_start = workday_start
    
    for booking in sorted_bookings:
        # Конвертируем время бронирования в часовой пояс бани для сравнения
        booking_start_local = booking.start_datetime.astimezone(BATHHOUSE_TIMEZONE)
        booking_end_local = booking.end_datetime.astimezone(BATHHOUSE_TIMEZONE)
        
        # If there's a gap before this booking, it's free
        if current_start < booking_start_local:
            free_intervals.append((current_start, booking_start_local))
        
        # Move current_start to the end of this booking
        if current_start < booking_end_local:
            current_start = booking_end_local
    
    # Check for free time after last booking
    if current_start < workday_end:
        free_intervals.append((current_start, workday_end))
    
    # Filter out zero-length intervals
    free_intervals = [(start, end) for start, end in free_intervals if start < end]
    
    return free_intervals


def merge_adjacent_intervals(intervals, gap_minutes=0) -> List[Tuple[datetime, datetime]]:
    """
    Merge adjacent or nearly adjacent intervals.
    
    Args:
        intervals: List of (start, end) tuples
        gap_minutes: Maximum gap to consider intervals as adjacent
    
    Returns:
        List of merged intervals
    """
    if not intervals:
        return []
    
    # Sort by start time
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    
    merged = []
    current_start, current_end = sorted_intervals[0]
    
    for interval_start, interval_end in sorted_intervals[1:]:
        # If intervals are adjacent or have small gap, merge them
        if interval_start <= current_end + timedelta(minutes=gap_minutes):
            current_end = max(current_end, interval_end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = interval_start, interval_end
    
    merged.append((current_start, current_end))
    return merged


def format_free_intervals(intervals) -> str:
    """
    Format free intervals for display.
    
    Args:
        intervals: List of (start_datetime, end_datetime) tuples
    
    Returns:
        Formatted string (empty string if no free intervals)
    """
    if not intervals:
        return ""
    
    # Format intervals
    interval_strings = []
    for interval_start, interval_end in intervals:
        start_str = interval_start.strftime("%H:%M")
        end_str = interval_end.strftime("%H:%M")
        interval_strings.append(f"{start_str}-{end_str}")
    
    if len(interval_strings) <= 3:
        return ", ".join(interval_strings)
    else:
        return ", ".join(interval_strings[:3]) + f" и еще {len(interval_strings) - 3}"
