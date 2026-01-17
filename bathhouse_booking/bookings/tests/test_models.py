from django.test import TestCase
from bathhouse_booking.bookings.models import Client, Bathhouse, Booking, SystemConfig
from django.core.exceptions import ValidationError
from django.utils import timezone

class ModelTests(TestCase):
    def test_create_client(self):
        client = Client.objects.create(  # type: ignore
            name="Иван Иванов",
            phone="+79123456789",
            telegram_id="123456789",
            comment="Тестовый клиент"
        )
        self.assertEqual(client.name, "Иван Иванов")
        self.assertEqual(str(client), "Иван Иванов (+79123456789)")
    
    def test_create_client_without_phone(self):
        client = Client.objects.create(  # type: ignore
            name="Иван Иванов",
            phone=None,
            telegram_id="123456789"
        )
        self.assertEqual(client.name, "Иван Иванов")
        self.assertEqual(str(client), "Иван Иванов (нет телефона)")
    
    def test_create_bathhouse(self):
        bathhouse = Bathhouse.objects.create(  # type: ignore
            name="Баня №1",
            capacity=5,
            is_active=True
        )
        self.assertEqual(bathhouse.name, "Баня №1")
        self.assertEqual(str(bathhouse), "Баня №1")
    
    def test_create_booking(self):
        client = Client.objects.create(name="Клиент", phone="+79123456789")  # type: ignore
        bathhouse = Bathhouse.objects.create(name="Баня")  # type: ignore
        start = timezone.now()
        end = start + timezone.timedelta(hours=2)
        
        booking = Booking.objects.create(  # type: ignore
            client=client,
            bathhouse=bathhouse,
            start_datetime=start,
            end_datetime=end,
            status="pending",
            price_total=5000,
            prepayment_amount=1000,
            comment="Тест"
        )
        self.assertEqual(booking.status, "pending")
        self.assertIn("Баня", str(booking))
    
    def test_booking_invalid_dates(self):
        client = Client.objects.create(name="Клиент", phone="+79123456789")  # type: ignore
        bathhouse = Bathhouse.objects.create(name="Баня")  # type: ignore
        start = timezone.now()
        end = start - timezone.timedelta(hours=1)
        
        booking = Booking(
            client=client,
            bathhouse=bathhouse,
            start_datetime=start,
            end_datetime=end,
            status="pending"
        )
        try:
            booking.full_clean()
            self.fail("Should raise ValidationError for invalid dates")
        except ValidationError as e:
            self.assertIn("start_datetime", str(e))
    
    def test_create_system_config(self):
        config = SystemConfig.objects.create(  # type: ignore
            key="OPEN_HOUR",
            value="9",
            description="Время открытия"
        )
        self.assertEqual(config.key, "OPEN_HOUR")
        self.assertEqual(str(config), "OPEN_HOUR")
    
    def test_system_config_contains_hourly_price(self):
        from bathhouse_booking.bookings.config_init import DEFAULT_CONFIGS
        hourly_price_configs = [c for c in DEFAULT_CONFIGS if c['key'] == 'HOURLY_PRICE']
        self.assertEqual(len(hourly_price_configs), 1, "HOURLY_PRICE should be in DEFAULT_CONFIGS")
        config = hourly_price_configs[0]
        self.assertEqual(config['key'], 'HOURLY_PRICE')
        self.assertIsInstance(config['value'], str)
        self.assertIn('Цена за час', config['description'])
    
    def test_booking_in_past_raises_error(self):
        client = Client.objects.create(name="Клиент", phone="+79123456789")  # type: ignore
        bathhouse = Bathhouse.objects.create(name="Баня")  # type: ignore
        past = timezone.now() - timezone.timedelta(hours=1)
        future = past + timezone.timedelta(hours=2)
        
        booking = Booking(
            client=client,
            bathhouse=bathhouse,
            start_datetime=past,
            end_datetime=future,
            status="pending"
        )
        try:
            booking.full_clean()
            self.fail("Should raise ValidationError for booking in past")
        except ValidationError as e:
            self.assertIn("start_datetime", str(e))
            self.assertIn("прошлом", str(e))

