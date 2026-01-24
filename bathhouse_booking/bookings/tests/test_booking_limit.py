from django.test import TestCase
from bathhouse_booking.bookings.models import Client, Bathhouse, Booking, SystemConfig
from bathhouse_booking.bookings import services
from bathhouse_booking.bookings.config_init import initialize_system_config
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class BookingLimitTests(TestCase):
    """Тесты ограничения бронирований (только approved)."""
    
    def setUp(self):
        # Инициализируем конфиги
        initialize_system_config()
        
        # Устанавливаем лимит 2 для тестов
        SystemConfig.objects.update_or_create(
            key="MAX_ACTIVE_BOOKINGS_PER_CLIENT",
            defaults={'value': '2', 'description': 'Лимит для тестов'}
        )
        
        # Создаем тестовые данные
        self.client = Client.objects.create(
            name="Тестовый Клиент для лимита",
            phone="+79123456789",
            telegram_id="111222333"
        )
        
        self.bathhouse = Bathhouse.objects.create(
            name="Тестовая Баня для лимита",
            capacity=5,
            is_active=True
        )
        
        # Временные интервалы
        self.start = timezone.now() + timedelta(hours=1)
        self.end = self.start + timedelta(hours=2)
    
    def test_booking_limit_with_approved_only(self):
        """Тест: лимит учитывает только approved бронирования."""
        print("=== Тест ограничения бронирований (только approved) ===")
        
        # Создаем 2 approved бронирования
        booking1 = Booking.objects.create(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status='approved',
            price_total=2000
        )
        print(f"✓ Создано approved бронирование #{booking1.id}")
        
        booking2 = Booking.objects.create(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start + timedelta(days=1),
            end_datetime=self.end + timedelta(days=1),
            status='approved',
            price_total=2000
        )
        print(f"✓ Создано approved бронирование #{booking2.id}")
        
        # Проверяем лимит - должно быть 2 approved (на пределе лимита)
        with self.assertRaises(ValidationError) as cm:
            services.check_booking_limit(self.client)
        print(f"✓ Лимит достигнут (2 approved): {cm.exception}")
        
        # Пытаемся создать третье approved через create_booking_request - должно быть ошибка
        with self.assertRaises(ValidationError) as cm:
            services.create_booking_request(
                client=self.client,
                bathhouse=self.bathhouse,
                start=self.start + timedelta(days=2),
                end=self.end + timedelta(days=2),
                comment="Третье бронирование"
            )
        print(f"✓ Третье approved бронирование заблокировано: {cm.exception}")
    
    def test_pending_bookings_not_counted(self):
        """Тест: pending бронирования не учитываются в лимите."""
        print("\n=== Тест: pending бронирования не учитываются ===")
        
        # Создаем 2 pending бронирования
        for i in range(2):
            Booking.objects.create(
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timedelta(days=i),
                end_datetime=self.end + timedelta(days=i),
                status='pending',
                price_total=2000
            )
        print("✓ Создано 2 pending бронирования")
        
        # Проверяем лимит - должно быть 0 approved
        try:
            services.check_booking_limit(self.client)
            print("✓ Лимит не превышен (0 approved, 2 pending)")
        except ValidationError as e:
            print(f"✗ Ошибка лимита: {e}")
            self.fail(f"Лимит не должен быть превышен при 0 approved: {e}")
        
        # Можем создать еще 2 approved (всего 2 approved + 2 pending)
        for i in range(2):
            Booking.objects.create(
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timedelta(days=i+2),
                end_datetime=self.end + timedelta(days=i+2),
                status='approved',
                price_total=2000
            )
        print("✓ Создано 2 approved бронирования (всего 2 approved + 2 pending)")
        
        # Проверяем лимит - должно быть 2 approved
        try:
            services.check_booking_limit(self.client)
            print("✓ Лимит не превышен (2 approved, 2 pending)")
        except ValidationError as e:
            print(f"✗ Ошибка лимита: {e}")
            self.fail(f"Лимит не должен быть превышен при 2 approved: {e}")
        
        # Пытаемся создать третье approved - должно быть ошибка
        with self.assertRaises(ValidationError) as cm:
            Booking.objects.create(
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timedelta(days=4),
                end_datetime=self.end + timedelta(days=4),
                status='approved',
                price_total=2000
            )
        print(f"✓ Третье approved заблокировано (лимит 2 approved)")
    
    def test_payment_reported_not_counted(self):
        """Тест: payment_reported статус не учитывается в лимите."""
        print("\n=== Тест: payment_reported не учитывается ===")
        
        # Создаем 2 payment_reported бронирования
        for i in range(2):
            Booking.objects.create(
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timedelta(days=i),
                end_datetime=self.end + timedelta(days=i),
                status='payment_reported',
                price_total=2000
            )
        print("✓ Создано 2 payment_reported бронирования")
        
        # Проверяем лимит - должно быть 0 approved
        try:
            services.check_booking_limit(self.client)
            print("✓ Лимит не превышен (0 approved, 2 payment_reported)")
        except ValidationError as e:
            print(f"✗ Ошибка лимита: {e}")
            self.fail(f"Лимит не должен быть превышен при 0 approved: {e}")
        
        # Можем создать 2 approved
        for i in range(2):
            Booking.objects.create(
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timedelta(days=i+2),
                end_datetime=self.end + timedelta(days=i+2),
                status='approved',
                price_total=2000
            )
        print("✓ Создано 2 approved бронирования")
        
        # Проверяем лимит - должно быть 2 approved
        try:
            services.check_booking_limit(self.client)
            print("✓ Лимит не превышен (2 approved, 2 payment_reported)")
        except ValidationError as e:
            print(f"✗ Ошибка лимита: {e}")
            self.fail(f"Лимит не должен быть превышен при 2 approved: {e}")
    
    def test_mixed_statuses_counting(self):
        """Тест: смешанные статусы, считаются только approved."""
        print("\n=== Тест: смешанные статусы ===")
        
        statuses = ['approved', 'pending', 'payment_reported', 'cancelled', 'rejected']
        
        for i, status in enumerate(statuses):
            Booking.objects.create(
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timedelta(days=i),
                end_datetime=self.end + timedelta(days=i),
                status=status,
                price_total=2000
            )
            print(f"✓ Создано {status} бронирование")
        
        # Должен быть только 1 approved (из 5 бронирований)
        try:
            services.check_booking_limit(self.client)
            print("✓ Лимит не превышен (1 approved из 5 бронирований)")
        except ValidationError as e:
            print(f"✗ Ошибка лимита: {e}")
            self.fail(f"Лимит не должен быть превышен при 1 approved: {e}")
        
        # Можем создать еще 1 approved (всего 2 approved)
        Booking.objects.create(
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start + timedelta(days=5),
            end_datetime=self.end + timedelta(days=5),
            status='approved',
            price_total=2000
        )
        print("✓ Создано второе approved бронирование")
        
        # Проверяем лимит - должно быть 2 approved
        try:
            services.check_booking_limit(self.client)
            print("✓ Лимит не превышен (2 approved из 6 бронирований)")
        except ValidationError as e:
            print(f"✗ Ошибка лимита: {e}")
            self.fail(f"Лимит не должен быть превышен при 2 approved: {e}")
        
        # Пытаемся создать третье approved - должно быть ошибка
        with self.assertRaises(ValidationError) as cm:
            Booking.objects.create(
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timedelta(days=6),
                end_datetime=self.end + timedelta(days=6),
                status='approved',
                price_total=2000
            )
        print(f"✓ Третье approved заблокировано (лимит 2 approved)")
    
    def test_create_booking_request_respects_limit(self):
        """Тест: create_booking_request учитывает лимит approved."""
        print("\n=== Тест: create_booking_request учитывает лимит ===")
        
        # Создаем 2 approved бронирования через сервис
        for i in range(2):
            booking = services.create_booking_request(
                client=self.client,
                bathhouse=self.bathhouse,
                start=self.start + timedelta(days=i),
                end=self.end + timedelta(days=i),
                comment=f"Тестовое бронирование {i+1}"
            )
            # Меняем статус на approved
            booking.status = 'approved'
            booking.save()
            print(f"✓ Создано approved бронирование #{booking.id}")
        
        # Пытаемся создать третье бронирование через сервис
        # Должно создаться как pending, но при проверке лимита approved будет ошибка
        booking3 = services.create_booking_request(
            client=self.client,
            bathhouse=self.bathhouse,
            start=self.start + timedelta(days=2),
            end=self.end + timedelta(days=2),
            comment="Третье бронирование"
        )
        print(f"✓ Создано pending бронирование #{booking3.id}")
        
        # Если попробуем изменить его на approved - должна быть ошибка
        with self.assertRaises(ValidationError) as cm:
            booking3.status = 'approved'
            booking3.save()
        print(f"✓ Нельзя изменить на approved (лимит 2 approved): {cm.exception}")
        
        # Но можно изменить на другой статус
        booking3.status = 'cancelled'
        booking3.save()
        print("✓ Можно изменить на cancelled")
    
    def test_error_message_in_russian(self):
        """Тест: сообщение об ошибке на русском языке."""
        print("\n=== Тест: сообщение об ошибке ===")
        
        # Создаем 2 approved бронирования
        for i in range(2):
            Booking.objects.create(
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timedelta(days=i),
                end_datetime=self.end + timedelta(days=i),
                status='approved',
                price_total=2000
            )
        
        # Пытаемся создать третье approved
        with self.assertRaises(ValidationError) as cm:
            Booking.objects.create(
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timedelta(days=2),
                end_datetime=self.end + timedelta(days=2),
                status='approved',
                price_total=2000
            )
        
        error_message = str(cm.exception)
        print(f"Сообщение об ошибке: {error_message}")
        
        # Проверяем, что сообщение на русском и содержит ключевые слова
        self.assertIn("подтвержденных бронирований", error_message.lower())
        self.assertIn("лимит", error_message.lower())
        print("✓ Сообщение об ошибке на русском языке")