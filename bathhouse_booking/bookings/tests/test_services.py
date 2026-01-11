from django.test import TestCase
from bookings.models import Client, Bathhouse, Booking
from bookings import services
from django.core.exceptions import ValidationError
from django.utils import timezone

class ServicesTests(TestCase):
    def setUp(self):
        self.client = Client.objects.create(name="Клиент", phone="+79123456789")  # type: ignore
        self.bathhouse = Bathhouse.objects.create(name="Баня")  # type: ignore
        self.start = timezone.now()
        self.end = self.start + timezone.timedelta(hours=2)
    
    def test_create_booking_request_creates_pending(self):
        booking = services.create_booking_request(
            client=self.client,
            bathhouse=self.bathhouse,
            start=self.start,
            end=self.end,
            comment="Тестовое бронирование"
        )
        
        self.assertEqual(booking.status, "pending")
        self.assertEqual(booking.client, self.client)
        self.assertEqual(booking.bathhouse, self.bathhouse)
        self.assertEqual(booking.comment, "Тестовое бронирование")
    
    def test_create_booking_request_invalid_dates_raises_error(self):
        with self.assertRaises(ValidationError):
            services.create_booking_request(
                client=self.client,
                bathhouse=self.bathhouse,
                start=self.end,  # start > end
                end=self.start,
                comment="Невалидные даты"
            )
    
    def test_report_payment_changes_status(self):
        booking = Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="pending"
        )
        
        services.report_payment(booking.id)
        booking.refresh_from_db()
        
        self.assertEqual(booking.status, "payment_reported")
    
    def test_approve_booking_changes_status(self):
        booking = Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="payment_reported"
        )
        
        services.approve_booking(booking.id)
        booking.refresh_from_db()
        
        self.assertEqual(booking.status, "approved")
    
    def test_approve_booking_overlap_prohibited(self):
        # Создаем approved бронирование
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="approved"
        )
        
        # Создаем второе бронирование с пересечением
        overlapping_booking = Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start + timezone.timedelta(hours=1),
            end_datetime=self.end + timezone.timedelta(hours=1),
            status="payment_reported"
        )
        
        # Попытка подтвердить второе бронирование должна вызвать ошибку
        with self.assertRaises(ValidationError):
            services.approve_booking(overlapping_booking.id)
        
        overlapping_booking.refresh_from_db()
        self.assertEqual(overlapping_booking.status, "payment_reported")  # статус не должен измениться
    
    def test_reject_booking_changes_status(self):
        booking = Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="pending"
        )
        
        services.reject_booking(booking.id, reason="Нет оплаты")
        booking.refresh_from_db()
        
        self.assertEqual(booking.status, "rejected")


    def test_services_raise_error_for_nonexistent_booking(self):
        with self.assertRaises(ValidationError):
            services.report_payment(99999)  # Несуществующий ID
        
        with self.assertRaises(ValidationError):
            services.approve_booking(99999)
        
        with self.assertRaises(ValidationError):
            services.reject_booking(99999, reason="Тест")

