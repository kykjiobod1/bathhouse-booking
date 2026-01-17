"""
Тесты для проверки обработки ошибок и логирования.
"""
import logging
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import DatabaseError

from bathhouse_booking.bookings.models import Client, Bathhouse, Booking
from bathhouse_booking.bookings import services
from django.utils import timezone


class ErrorHandlingTests(TestCase):
    """Тесты обработки ошибок в сервисах."""
    
    def setUp(self):
        self.client = Client.objects.create(name="Клиент", phone="+79123456789")  # type: ignore
        self.bathhouse = Bathhouse.objects.create(name="Баня")  # type: ignore
        self.start = timezone.now() + timezone.timedelta(hours=1)  # будущее время, чтобы пройти проверку прошлого
        self.end = self.start + timezone.timedelta(hours=2)
        
        # Создаем тестовое бронирование
        self.booking = Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="pending"
        )
    
    def test_create_booking_request_validation_error(self):
        """Проверка обработки ValidationError при создании бронирования."""
        with self.assertRaises(ValidationError):
            # Пытаемся создать бронирование с невалидными датами
            services.create_booking_request(
                client=self.client,
                bathhouse=self.bathhouse,
                start=self.end,  # start > end
                end=self.start,
                comment="Невалидные даты"
            )
    
    def test_create_booking_request_database_error(self):
        """Проверка обработки DatabaseError при создании бронирования."""
        with patch('bathhouse_booking.bookings.services.Booking.objects.filter') as mock_filter:
            mock_filter.side_effect = DatabaseError("Database connection failed")
            
            with self.assertRaises(DatabaseError):
                services.create_booking_request(
                    client=self.client,
                    bathhouse=self.bathhouse,
                    start=self.start,
                    end=self.end
                )
    
    def test_report_payment_booking_not_found(self):
        """Проверка обработки случая, когда бронирование не найдено."""
        with self.assertRaises(ValidationError) as cm:
            # Пытаемся отметить оплату для несуществующего бронирования
            services.report_payment(99999)
        
        self.assertIn("Бронирование с ID 99999 не найдено", str(cm.exception))
    
    def test_approve_booking_validation_error(self):
        """Проверка обработки ValidationError при подтверждении бронирования."""
        # Создаем пересекающееся approved бронирование
        overlapping_booking = Booking.objects.create(  # type: ignore
            client=self.client,
            bathhouse=self.bathhouse,
            start_datetime=self.start,
            end_datetime=self.end,
            status="approved"
        )
        
        with self.assertRaises(ValidationError) as cm:
            # Пытаемся подтвердить бронирование с пересечением
            services.approve_booking(self.booking.id)
        
        self.assertIn("Пересечение с другим подтвержденным бронированием", str(cm.exception))
    
    def test_cancel_booking_invalid_status(self):
        """Проверка обработки при попытке отменить бронирование с невалидным статусом."""
        # Меняем статус бронирования на approved (нельзя отменить)
        self.booking.status = "approved"
        self.booking.save()
        
        with self.assertRaises(ValidationError) as cm:
            # Пытаемся отменить бронирование со статусом approved
            services.cancel_booking(self.booking.id)
        
        self.assertIn("Нельзя отменить бронирование со статусом approved", str(cm.exception))
    
    def test_get_available_slots_database_error(self):
        """Проверка обработки DatabaseError при получении доступных слотов."""
        with patch('bathhouse_booking.bookings.services.Booking.objects.filter') as mock_filter:
            mock_filter.side_effect = DatabaseError("Database connection failed")
            
            with self.assertRaises(DatabaseError):
                services.get_available_slots(self.bathhouse, self.start.date())
    
    def test_service_functions_work_correctly(self):
        """Проверка, что сервисные функции работают корректно."""
        # Проверяем report_payment
        services.report_payment(self.booking.id)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "payment_reported")
        
        # Проверяем approve_booking (после изменения статуса на payment_reported)
        services.approve_booking(self.booking.id)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "approved")


class BotErrorHandlingTests(TestCase):
    """Тесты обработки ошибок в боте."""
    
    def test_bot_error_handler_import(self):
        """Проверка, что модуль обработки ошибок бота импортируется."""
        try:
            from bathhouse_booking.bot.error_handlers import error_handler, setup_error_handlers
            self.assertTrue(callable(error_handler))
            self.assertTrue(callable(setup_error_handlers))
        except ImportError as e:
            self.fail(f"Failed to import bot error handlers: {e}")


class LoggingConfigurationTests(TestCase):
    """Тесты конфигурации логирования."""
    
    def test_logging_configuration_exists(self):
        """Проверка, что конфигурация логирования настроена."""
        from django.conf import settings
        
        self.assertIn('LOGGING', dir(settings))
        self.assertIsInstance(settings.LOGGING, dict)
        self.assertEqual(settings.LOGGING['version'], 1)
    
    def test_loggers_configured(self):
        """Проверка, что логгеры настроены."""
        from django.conf import settings
        
        loggers = settings.LOGGING.get('loggers', {})
        
        # Проверяем основные логгеры
        self.assertIn('django', loggers)
        self.assertIn('bookings', loggers)
        self.assertIn('bot', loggers)
        self.assertIn('services', loggers)
    
    def test_log_files_directory_exists(self):
        """Проверка, что директория для логов существует."""
        import os
        from pathlib import Path
        
        logs_dir = Path(__file__).parent.parent.parent / 'logs'
        self.assertTrue(logs_dir.exists(), f"Logs directory does not exist: {logs_dir}")
    
    def test_logging_levels(self):
        """Проверка уровней логирования."""
        from django.conf import settings
        
        loggers = settings.LOGGING.get('loggers', {})
        
        # Проверяем уровни для основных логгеров
        self.assertEqual(loggers.get('django', {}).get('level'), 'INFO')
        self.assertEqual(loggers.get('django.request', {}).get('level'), 'ERROR')
        self.assertEqual(loggers.get('bookings', {}).get('level'), 'INFO')
        self.assertEqual(loggers.get('bot', {}).get('level'), 'INFO')