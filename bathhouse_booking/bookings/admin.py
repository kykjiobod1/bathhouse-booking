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
    list_display = ['client', 'bathhouse', 'start_datetime', 'end_datetime', 'status', 'price_total', 'created_at']
    list_filter = ['status', 'bathhouse', 'start_datetime']
    search_fields = ['client__name', 'client__phone', 'comment']
    readonly_fields = ['created_at']
    date_hierarchy = 'start_datetime'
    ordering = ('-start_datetime',)
    list_select_related = ('client', 'bathhouse')


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'description']
    search_fields = ['key', 'description']
