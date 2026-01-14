import pytest
from django.test import TestCase
from bathhouse_booking.bookings.models import Bathhouse, Booking, Client
from bathhouse_booking.bookings import services
from django.utils import timezone
from datetime import datetime, time, timedelta
import pytz

class TestServicesIntegration(TestCase):
    def setUp(self):
        self.bathhouse = Bathhouse.objects.create(name="Test Bathhouse", is_active=True)
        self.client = Client.objects.create(name="Test Client", phone="+123", telegram_id="123")
        self.test_date = datetime(2024, 1, 1).date()
        self.tz = pytz.timezone('UTC')

    def test_get_free_intervals(self):
        """Test get_free_intervals function"""
        # Test 1: No bookings (whole day free)
        intervals = services.get_free_intervals(self.bathhouse, self.test_date)
        self.assertGreater(len(intervals), 0)
        
        # Test 2: With bookings
        booking1 = Booking.objects.create(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.tz.localize(datetime.combine(self.test_date, time(10, 0))),
            end_datetime=self.tz.localize(datetime.combine(self.test_date, time(12, 0))),
            status="approved"
        )
        
        booking2 = Booking.objects.create(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.tz.localize(datetime.combine(self.test_date, time(14, 0))),
            end_datetime=self.tz.localize(datetime.combine(self.test_date, time(16, 0))),
            status="approved"
        )
        
        intervals = services.get_free_intervals(self.bathhouse, self.test_date)
        self.assertGreater(len(intervals), 0)
        
        # Test 3: Merge adjacent intervals
        merged = services.merge_adjacent_intervals(intervals, gap_minutes=30)
        self.assertIsInstance(merged, list)
        
        # Test 4: Format intervals
        formatted = services.format_free_intervals(merged)
        self.assertIsInstance(formatted, str)