from django.core.exceptions import ValidationError
from django.db import DatabaseError
from .models import Booking, SystemConfig
from django.utils import timezone
from datetime import datetime, time, timedelta
from typing import List, Tuple

def create_booking_request(client, bathhouse, start, end, comment=None):
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
    return booking

def report_payment(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)  # type: ignore
    except Booking.DoesNotExist:  # type: ignore
        raise ValidationError(f"Бронирование с ID {booking_id} не найдено")

    booking.status = "payment_reported"
    booking.full_clean()
    booking.save()

def approve_booking(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)  # type: ignore
    except Booking.DoesNotExist:  # type: ignore
        raise ValidationError(f"Бронирование с ID {booking_id} не найдено")

    booking.status = "approved"
    booking.full_clean()
    booking.save()

def reject_booking(booking_id, reason=None):
    try:
        booking = Booking.objects.get(id=booking_id)  # type: ignore
    except Booking.DoesNotExist:  # type: ignore
        raise ValidationError(f"Бронирование с ID {booking_id} не найдено")

    booking.status = "rejected"
    if reason:
        booking.comment = f"{booking.comment}\nОтклонено: {reason}" if booking.comment else f"Отклонено: {reason}"
    booking.full_clean()
    booking.save()


def get_available_slots(bathhouse, date) -> List[Tuple[datetime, datetime]]:
    # Получаем настройки из SystemConfig
    def get_config(key, default):
        try:
            config = SystemConfig.objects.get(key=key)  # type: ignore
            return int(config.value)
        except SystemConfig.DoesNotExist:  # type: ignore
            return default
    
    open_hour = get_config("OPEN_HOUR", 9)
    close_hour = get_config("CLOSE_HOUR", 22)
    slot_step_minutes = get_config("SLOT_STEP_MINUTES", 30)
    min_booking_minutes = get_config("MIN_BOOKING_MINUTES", 120)
    
    # Получаем approved бронирования на эту дату для этой бани
    start_of_day = timezone.make_aware(datetime.combine(date, time(0, 0)))
    end_of_day = timezone.make_aware(datetime.combine(date, time(23, 59, 59)))
    
    approved_bookings = Booking.objects.filter(  # type: ignore
        bathhouse=bathhouse,
        status="approved",
        start_datetime__lt=end_of_day,
        end_datetime__gt=start_of_day
    )
    
    # Генерируем все возможные слоты
    slots = []
    current_time = timezone.make_aware(datetime.combine(date, time(open_hour, 0)))
    end_time = timezone.make_aware(datetime.combine(date, time(close_hour, 0)))
    
    while current_time < end_time:
        slot_start = current_time
        slot_end = slot_start + timedelta(minutes=min_booking_minutes)
        
        if slot_end <= end_time:
            # Проверяем пересечение с approved бронированиями
            overlaps = False
            for booking in approved_bookings:
                if not (slot_end <= booking.start_datetime or slot_start >= booking.end_datetime):
                    overlaps = True
                    break
            
            if not overlaps:
                slots.append((slot_start, slot_end))
        
        current_time += timedelta(minutes=slot_step_minutes)
    
    return slots
