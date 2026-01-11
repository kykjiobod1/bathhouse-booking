from django.core.exceptions import ValidationError
from django.db import DatabaseError
from .models import Booking

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
