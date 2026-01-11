from django.test import TestCase
from bookings.models import Client, Bathhouse, Booking
from django.core.exceptions import ValidationError
from django.utils import timezone

class BookingCleanTests(TestCase):
    def setUp(self):
        self.client = Client.objects.create(name="Клиент", phone="+79123456789")  # type: ignore
        self.bathhouse = Bathhouse.objects.create(name="Баня")  # type: ignore
        self.start = timezone.now()
        self.end = self.start + timezone.timedelta(hours=2)
    
    def test_invalid_range_raises_validation_error(self):
        booking = Booking(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.start,  # start == end
            status="pending"
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()
    
    def test_approved_overlap_prohibited_new_booking(self):
        # Создаем approved бронирование
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="approved"
        )
        
        # Пытаемся создать второе approved бронирование с пересечением
        overlapping_start = self.start + timezone.timedelta(hours=1)
        overlapping_end = self.end + timezone.timedelta(hours=1)
        booking2 = Booking(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=overlapping_start,
            end_datetime=overlapping_end,
            status="approved"
        )
        
        with self.assertRaises(ValidationError):
            booking2.full_clean()
    
    def test_approved_overlap_prohibited_update_booking(self):
        # Создаем pending бронирование
        booking = Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="pending"
        )
        
        # Создаем другое approved бронирование с пересечением
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start + timezone.timedelta(hours=1),
            end_datetime=self.end + timezone.timedelta(hours=1),
            status="approved"
        )
        
        # Пытаемся обновить первое бронирование на approved
        booking.status = "approved"
        with self.assertRaises(ValidationError):
            booking.full_clean()
    
    def test_pending_overlap_allowed(self):
        # Создаем pending бронирование
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="pending"
        )
        
        # Создаем второе pending бронирование с пересечением - должно быть разрешено
        overlapping_start = self.start + timezone.timedelta(hours=1)
        overlapping_end = self.end + timezone.timedelta(hours=1)
        booking2 = Booking(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=overlapping_start,
            end_datetime=overlapping_end,
            status="pending"
        )
        
        try:
            booking2.full_clean()
        except ValidationError:
            self.fail("Pending overlap should be allowed")
    
    def test_payment_reported_overlap_allowed(self):
        # Создаем payment_reported бронирование
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="payment_reported"
        )
        
        # Создаем второе payment_reported бронирование с пересечением - должно быть разрешено
        overlapping_start = self.start + timezone.timedelta(hours=1)
        overlapping_end = self.end + timezone.timedelta(hours=1)
        booking2 = Booking(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=overlapping_start,
            end_datetime=overlapping_end,
            status="payment_reported"
        )
        
        try:
            booking2.full_clean()
        except ValidationError:
            self.fail("Payment reported overlap should be allowed")
    
    def test_rejected_overlap_allowed(self):
        # Создаем rejected бронирование
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="rejected"
        )
        
        # Создаем второе rejected бронирование с пересечением - должно быть разрешено
        overlapping_start = self.start + timezone.timedelta(hours=1)
        overlapping_end = self.end + timezone.timedelta(hours=1)
        booking2 = Booking(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=overlapping_start,
            end_datetime=overlapping_end,
            status="rejected"
        )
        
        try:
            booking2.full_clean()
        except ValidationError:
            self.fail("Rejected overlap should be allowed")
    
    def test_cancelled_overlap_allowed(self):
        # Создаем cancelled бронирование
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="cancelled"
        )
        
        # Создаем второе cancelled бронирование с пересечением - должно быть разрешено
        overlapping_start = self.start + timezone.timedelta(hours=1)
        overlapping_end = self.end + timezone.timedelta(hours=1)
        booking2 = Booking(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=overlapping_start,
            end_datetime=overlapping_end,
            status="cancelled"
        )
        
        try:
            booking2.full_clean()
        except ValidationError:
            self.fail("Cancelled overlap should be allowed")

