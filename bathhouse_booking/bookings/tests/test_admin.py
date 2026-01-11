from django.test import TestCase
from bookings.models import Client, Bathhouse, Booking, SystemConfig


class TestAdminRegistration(TestCase):
    """Smoke test to ensure models are registered in admin"""
    
    def test_admin_site_has_models_registered(self):
        from django.contrib import admin
        self.assertIn(Client, admin.site._registry)
        self.assertIn(Bathhouse, admin.site._registry)
        self.assertIn(Booking, admin.site._registry)
        self.assertIn(SystemConfig, admin.site._registry)