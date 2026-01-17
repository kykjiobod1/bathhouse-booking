from django.db import models
from django.db import models
from django.core.exceptions import ValidationError
from django.apps import apps
from django.utils import timezone


class Client(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    telegram_id = models.CharField(max_length=64, null=True, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self) -> str:
        phone_display = self.phone if self.phone else "нет телефона"
        return f"{self.name} ({phone_display})"  # type: ignore


class Bathhouse(models.Model):
    name = models.CharField(max_length=200)
    capacity = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)  # type: ignore



    def __str__(self) -> str:
        return self.name  # type: ignore


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('payment_reported', 'Оплата сообщена'),
        ('approved', 'Подтверждено'),
        ('rejected', 'Отклонено'),
        ('cancelled', 'Отменено'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    bathhouse = models.ForeignKey(Bathhouse, on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    price_total = models.IntegerField(null=True, blank=True)
    prepayment_amount = models.IntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self) -> str:
        return f"{self.bathhouse.name} - {self.client.name} ({self.start_datetime:%Y-%m-%d %H:%M})"

    def clean(self):
        # Проверка наличия обязательных полей
        if self.start_datetime is None or self.end_datetime is None:
            raise ValidationError({
                'start_datetime': 'Время начала обязательно',
                'end_datetime': 'Время окончания обязательно'
            })
        
        # Проверка: start_datetime < end_datetime
        if self.start_datetime >= self.end_datetime:
            raise ValidationError({
                'start_datetime': 'Время начала должно быть раньше времени окончания',
                'end_datetime': 'Время окончания должно быть позже времени начала'
            })
        
        # Запрет бронирования в прошлое
        if self.start_datetime < timezone.now():
            raise ValidationError({
                'start_datetime': 'Время начала не может быть в прошлом',
                'end_datetime': 'Время начала не может быть в прошлом'
            })
        
        # Запрет пересечений только для approved статуса
        if self.status == 'approved':
            # Ищем пересекающиеся approved бронирования для той же бани
            overlapping_bookings = Booking.objects.filter(  # type: ignore
                bathhouse=self.bathhouse,
                status='approved',
                # Проверка пересечения: (start < existing.end) AND (end > existing.start)
                start_datetime__lt=self.end_datetime,
                end_datetime__gt=self.start_datetime
            )
            
            # Исключаем сам объект при обновлении существующей записи
            if self.pk:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.pk)
            
            if overlapping_bookings.exists():
                raise ValidationError({
                    'start_datetime': 'Пересечение с другим подтвержденным бронированием',
                    'end_datetime': 'Пересечение с другим подтвержденным бронированием'
                })


class SystemConfig(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)



    def __str__(self) -> str:
        return self.key  # type: ignore


class NotificationQueue(models.Model):
    """Очередь уведомлений для отправки через бота"""
    telegram_id = models.CharField(max_length=64)
    message = models.TextField()
    booking_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    attempts = models.IntegerField(default=0)



    def __str__(self) -> str:
        return f"Notification to {self.telegram_id} ({self.status})"
