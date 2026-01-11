from aiogram import Router

from .handlers import start, booking

router = Router()

router.include_router(start.router)
router.include_router(booking.router)