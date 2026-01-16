# Setup Django before importing handlers
import os
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathhouse_booking.config.settings')
import django
django.setup()

from aiogram import Router

from .handlers import start, booking, admin, my_bookings, message_admin, phone

router = Router()

router.include_router(start.router)
router.include_router(booking.router)
router.include_router(admin.router)
router.include_router(my_bookings.router)
router.include_router(message_admin.router)
router.include_router(phone.router)