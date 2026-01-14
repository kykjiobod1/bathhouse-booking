import pytz
from django.test import TestCase
from django.utils import timezone
from bathhouse_booking.bookings.models import Client, Bathhouse, Booking


class TimezoneTests(TestCase):
    def setUp(self):
        self.client = Client.objects.create(name="Test Client", phone="+123456789", telegram_id="123")
        self.bathhouse = Bathhouse.objects.create(name="Test Bathhouse", capacity=5, is_active=True)

    def test_booking_timezone_conversion_to_gmt_plus_7(self):
        """Test that booking times are correctly handled in GMT+7 timezone"""
        # Create booking with UTC time
        utc_tz = pytz.UTC
        gmt_plus_7_tz = pytz.timezone('Asia/Jakarta')
        
        # Set start time as 9:00 in GMT+7, which should be 2:00 UTC
        start_local = gmt_plus_7_tz.localize(timezone.datetime(2025, 1, 14, 9, 0, 0))
        end_local = gmt_plus_7_tz.localize(timezone.datetime(2025, 1, 14, 11, 0, 0))
        
        # Convert to UTC for storage
        start_utc = start_local.astimezone(utc_tz)
        end_utc = end_local.astimezone(utc_tz)
        
        # Create booking
        booking = Booking.objects.create(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=start_utc,
            end_datetime=end_utc,
            status="pending",
            price_total=5000
        )
        
        # Verify that when converted back to GMT+7, it shows correct time
        start_in_gmt7 = booking.start_datetime.astimezone(gmt_plus_7_tz)
        end_in_gmt7 = booking.end_datetime.astimezone(gmt_plus_7_tz)
        
        self.assertEqual(start_in_gmt7.hour, 9)
        self.assertEqual(start_in_gmt7.minute, 0)
        self.assertEqual(end_in_gmt7.hour, 11)
        self.assertEqual(end_in_gmt7.minute, 0)
        
        # Also test that Django's TIME_ZONE setting affects display
        from django.conf import settings
        self.assertEqual(settings.TIME_ZONE, 'Asia/Jakarta')