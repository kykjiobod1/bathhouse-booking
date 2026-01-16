from django.test import TestCase
from bathhouse_booking.bookings.models import Client, Bathhouse, Booking
from bathhouse_booking.bookings import services
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import time

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
    
    def test_create_booking_request_limit_checking(self):
        # Создаем SystemConfig с лимитом 2 бронирования
        from bathhouse_booking.bookings.models import SystemConfig
        SystemConfig.objects.create(key="MAX_ACTIVE_BOOKINGS_PER_CLIENT", value="2")  # type: ignore
        
        # Создаем 2 активных бронирования
        for i in range(2):
            Booking.objects.create(  # type: ignore
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timezone.timedelta(hours=i*3),
                end_datetime=self.end + timezone.timedelta(hours=i*3),
                status="pending"
            )
        
        # Попытка создать третье бронирование должна вызвать ошибку
        with self.assertRaises(ValidationError) as cm:
            services.create_booking_request(
                client=self.client,
                bathhouse=self.bathhouse,
                start=self.start + timezone.timedelta(hours=6),
                end=self.end + timezone.timedelta(hours=6)
            )
        
        error_message = str(cm.exception)
        self.assertIn("У вас уже есть", error_message)
        self.assertIn("активных бронирований", error_message)
        self.assertIn("Максимально допустимое количество: 2", error_message)
    
    def test_create_booking_request_limit_not_reached(self):
        # Создаем SystemConfig с лимитом 3 бронирования
        from bathhouse_booking.bookings.models import SystemConfig
        SystemConfig.objects.create(key="MAX_ACTIVE_BOOKINGS_PER_CLIENT", value="3")  # type: ignore
        
        # Создаем 2 активных бронирования (меньше лимита)
        for i in range(2):
            Booking.objects.create(  # type: ignore
                client=self.client,
                bathhouse=self.bathhouse,
                start_datetime=self.start + timezone.timedelta(hours=i*3),
                end_datetime=self.end + timezone.timedelta(hours=i*3),
                status="pending"
            )
        
        # Создание третьего бронирования должно пройти успешно
        booking = services.create_booking_request(
            client=self.client,
            bathhouse=self.bathhouse,
            start=self.start + timezone.timedelta(hours=6),
            end=self.end + timezone.timedelta(hours=6)
        )
        
        self.assertEqual(booking.status, "pending")
        self.assertEqual(booking.client, self.client)
        self.assertEqual(booking.bathhouse, self.bathhouse)
    
    def test_create_booking_request_only_active_bookings_counted(self):
        # Создаем SystemConfig с лимитом 2 бронирования
        from bathhouse_booking.bookings.models import SystemConfig
        SystemConfig.objects.create(key="MAX_ACTIVE_BOOKINGS_PER_CLIENT", value="2")  # type: ignore
        
        # Создаем 1 активное бронирование
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="pending"
        )
        
        # Создаем 1 неактивное бронирование (отклоненное)
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start + timezone.timedelta(hours=3),
            end_datetime=self.end + timezone.timedelta(hours=3),
            status="rejected"
        )
        
        # Создаем 1 неактивное бронирование (отмененное)
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start + timezone.timedelta(hours=6),
            end_datetime=self.end + timezone.timedelta(hours=6),
            status="cancelled"
        )
        
        # Создание второго активного бронирования должно пройти успешно
        # (только pending считается активным)
        booking = services.create_booking_request(
            client=self.client,
            bathhouse=self.bathhouse,
            start=self.start + timezone.timedelta(hours=9),
            end=self.end + timezone.timedelta(hours=9)
        )
        
        self.assertEqual(booking.status, "pending")
    
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


class GetAvailableSlotsTests(TestCase):
    def setUp(self):
        self.client = Client.objects.create(name="Клиент", phone="+79123456789")  # type: ignore
        self.bathhouse = Bathhouse.objects.create(name="Баня")  # type: ignore
        # Создаем SystemConfig с настройками по умолчанию
        from bathhouse_booking.bookings.models import SystemConfig
        SystemConfig.objects.create(key="OPEN_HOUR", value="9")  # type: ignore
        SystemConfig.objects.create(key="CLOSE_HOUR", value="22")  # type: ignore
        SystemConfig.objects.create(key="SLOT_STEP_MINUTES", value="30")  # type: ignore
        SystemConfig.objects.create(key="MIN_BOOKING_MINUTES", value="120")  # type: ignore
    
    def test_get_available_slots_no_bookings(self):
        date = timezone.now().date()
        slots = services.get_available_slots(self.bathhouse, date)
        
        # С 9:00 до 22:00 с шагом 30 минут, минимальная длительность 120 минут
        # Должны быть слоты: 9:00-11:00, 9:30-11:30, ..., 20:00-22:00
        self.assertGreater(len(slots), 0)
        for start, end in slots:
            self.assertEqual(start.date(), date)
            self.assertEqual(end.date(), date)
            duration = (end - start).total_seconds() / 60
            self.assertGreaterEqual(duration, 120)
    
    def test_get_available_slots_with_approved_booking(self):
        date = timezone.now().date()
        # Создаем approved бронирование с 10:00 до 12:00
        booking_start = timezone.make_aware(timezone.datetime.combine(date, time(10, 0)))
        booking_end = timezone.make_aware(timezone.datetime.combine(date, time(12, 0)))
        
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=booking_start,
            end_datetime=booking_end,
            status="approved"
        )
        
        slots = services.get_available_slots(self.bathhouse, date)
        
        # Слоты, пересекающиеся с 10:00-12:00, должны быть исключены
        for start, end in slots:
            # Проверяем, что слот не пересекается с бронированием
            self.assertTrue(end <= booking_start or start >= booking_end)
    
    def test_get_available_slots_working_hours(self):
        date = timezone.now().date()
        slots = services.get_available_slots(self.bathhouse, date)
        
        # Все слоты должны быть в пределах рабочих часов 9:00-22:00
        for start, end in slots:
            self.assertGreaterEqual(start.hour, 9)
            self.assertLessEqual(end.hour, 22)
            if end.hour == 22:
                self.assertEqual(end.minute, 0)
    
    def test_get_available_slots_minimum_duration(self):
        date = timezone.now().date()
        slots = services.get_available_slots(self.bathhouse, date)
        
        # Все слоты должны быть не менее 120 минут
        for start, end in slots:
            duration = (end - start).total_seconds() / 60
            self.assertGreaterEqual(duration, 120)
    
    def test_get_available_slots_non_approved_bookings_ignored(self):
        date = timezone.now().date()
        # Создаем pending бронирование с 10:00 до 12:00
        booking_start = timezone.make_aware(timezone.datetime.combine(date, time(10, 0)))
        booking_end = timezone.make_aware(timezone.datetime.combine(date, time(12, 0)))
        
        Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=booking_start,
            end_datetime=booking_end,
            status="pending"
        )
        
        slots = services.get_available_slots(self.bathhouse, date)
        
        # Pending бронирование не должно влиять на доступные слоты
        # Проверяем, что есть слоты, пересекающиеся с 10:00-12:00
        has_overlapping_slot = False
        for start, end in slots:
            if not (end <= booking_start or start >= booking_end):
                has_overlapping_slot = True
                break
        
        self.assertTrue(has_overlapping_slot, "Pending booking should not block slots")

