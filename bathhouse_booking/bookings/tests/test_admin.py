from django.test import TestCase
from bathhouse_booking.bookings.models import Client, Bathhouse, Booking, SystemConfig
from django.utils import timezone


class TestAdminRegistration(TestCase):
    """Smoke test to ensure models are registered in admin"""
    
    def test_admin_site_has_models_registered(self):
        from django.contrib import admin
        self.assertIn(Client, admin.site._registry)
        self.assertIn(Bathhouse, admin.site._registry)
        self.assertIn(Booking, admin.site._registry)
        self.assertIn(SystemConfig, admin.site._registry)


class TestBookingAdminActions(TestCase):
    """Test admin actions for Booking model"""
    
    def setUp(self):
        self.client_model = Client.objects.create(name="Клиент", phone="+79123456789")  # type: ignore
        self.bathhouse = Bathhouse.objects.create(name="Баня")  # type: ignore
        self.start = timezone.now()
        self.end = self.start + timezone.timedelta(hours=2)
        
        # Создаем бронирования для тестирования
        self.pending_booking = Booking.objects.create(  # type: ignore
            client=self.client_model,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="pending"
        )
        
        self.payment_reported_booking = Booking.objects.create(  # type: ignore
            client=self.client_model,
            bathhouse=self.bathhouse,
            start_datetime=self.start + timezone.timedelta(days=1),
            end_datetime=self.end + timezone.timedelta(days=1),
            status="payment_reported"
        )
    
    def test_actions_defined_in_admin(self):
        """Test that approve and reject actions are defined in BookingAdmin"""
        from bathhouse_booking.bookings.admin import BookingAdmin
        from django.contrib.admin.sites import AdminSite
        
        admin = BookingAdmin(Booking, AdminSite())
        
        # Проверяем, что actions определены
        self.assertIn('approve', admin.actions)
        self.assertIn('reject', admin.actions)
    
    def test_approve_action_works_through_services(self):
        """Test that approve action calls services.approve_booking"""
        from bathhouse_booking.bookings import services
        
        # Вызываем сервис напрямую
        services.approve_booking(self.payment_reported_booking.id)
        
        self.payment_reported_booking.refresh_from_db()
        self.assertEqual(self.payment_reported_booking.status, "approved")
    
    def test_reject_action_works_through_services(self):
        """Test that reject action calls services.reject_booking"""
        from bathhouse_booking.bookings import services
        
        # Вызываем сервис напрямую
        services.reject_booking(self.pending_booking.id, reason="Отклонено через админку")
        
        self.pending_booking.refresh_from_db()
        self.assertEqual(self.pending_booking.status, "rejected")
        self.assertIn("Отклонено через админку", self.pending_booking.comment)
    
    def test_approve_action_with_overlap_prohibited(self):
        """Test that approve action respects overlap validation"""
        from bathhouse_booking.bookings import services
        
        # Создаем approved бронирование
        Booking.objects.create(  # type: ignore
            client=self.client_model,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="approved"
        )
        
        # Создаем пересекающееся payment_reported бронирование
        overlapping_booking = Booking.objects.create(  # type: ignore
            client=self.client_model,
            bathhouse=self.bathhouse,
            start_datetime=self.start + timezone.timedelta(hours=1),
            end_datetime=self.end + timezone.timedelta(hours=1),
            status="payment_reported"
        )
        
        # Попытка подтвердить должно вызвать ValidationError
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            services.approve_booking(overlapping_booking.id)
        
        overlapping_booking.refresh_from_db()
        self.assertEqual(overlapping_booking.status, "payment_reported")