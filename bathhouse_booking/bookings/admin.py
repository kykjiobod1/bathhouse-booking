from django.contrib import admin
from .models import Client, Bathhouse, Booking, SystemConfig

admin.site.site_header = "Удачи!!"
admin.site.site_title = "Удачи!!"
admin.site.index_title = "Удачи!!"


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'telegram_id', 'created_at']
    search_fields = ['name', 'phone', 'telegram_id']


@admin.register(Bathhouse)
class BathhouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'is_active']
    list_filter = ['is_active']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['client', 'bathhouse', 'start_datetime', 'end_datetime', 'status', 'price_total', 'comment', 'created_at']
    list_filter = ['status', 'bathhouse', 'start_datetime']
    search_fields = ['client__name', 'client__phone', 'comment']
    readonly_fields = ['created_at', 'prepayment_amount']
    date_hierarchy = 'start_datetime'
    ordering = ('-start_datetime',)
    list_select_related = ('client', 'bathhouse')
    actions = ['approve', 'reject']
    
    def save_model(self, request, obj, form, change):
        """Запретить установку статуса payment_reported через прямое редактирование."""
        if change and 'status' in form.changed_data:
            # Если пытаемся изменить статус
            from .models import Booking
            old_status = Booking.objects.get(pk=obj.pk).status
            new_status = obj.status
            
            # Запрещаем установку payment_reported через админку
            if new_status == 'payment_reported':
                from django.contrib import messages
                messages.error(
                    request,
                    "Статус 'Оплата сообщена' нельзя установить через прямое редактирование. "
                    "Используйте действие 'Подтвердить выбранные бронирования'."
                )
                # Восстанавливаем старый статус
                obj.status = old_status
        
        super().save_model(request, obj, form, change)
    
    @admin.action(description="Подтвердить выбранные бронирования")
    def approve(self, request, queryset):
        from .services import approve_booking
        from django.contrib import messages

        success_count = 0
        error_count = 0

        for booking in queryset:
            try:
                # Проверяем, что у клиента есть telegram_id для уведомлений
                if not booking.client.telegram_id:
                    self.message_user(
                        request,
                        f"У клиента {booking.client} нет telegram_id. Уведомление не будет отправлено.",
                        messages.WARNING
                    )
                approve_booking(booking.id)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Ошибка при подтверждении бронирования {booking.id}: {str(e)}",
                    messages.ERROR
                )

        if success_count:
            self.message_user(
                request,
                f"Подтверждено бронирований: {success_count}",
                messages.SUCCESS
            )
    
    @admin.action(description="Отклонить выбранные бронирования")
    def reject(self, request, queryset):
        from .services import reject_booking
        from django.contrib import messages
        
        success_count = 0
        error_count = 0
        
        for booking in queryset:
            try:
                # Проверяем, что у клиента есть telegram_id для уведомлений
                if not booking.client.telegram_id:
                    self.message_user(
                        request,
                        f"У клиента {booking.client} нет telegram_id. Уведомление не будет отправлено.",
                        messages.WARNING
                    )
                reject_booking(booking.id)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Ошибка при подтверждении бронирования {booking.id}: {str(e)}",
                    messages.ERROR
                )
        
        if success_count:
            self.message_user(
                request,
                f"Отклонено бронирований: {success_count}",
                messages.SUCCESS
            )
    



@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'description']
    search_fields = ['key', 'description']
