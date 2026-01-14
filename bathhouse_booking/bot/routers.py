# Setup Django before importing handlers
import os
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathhouse_booking.config.settings')
import django
django.setup()

from aiogram import Router

from .handlers import start, booking

router = Router()

router.include_router(start.router)
router.include_router(booking.router)