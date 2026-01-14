from aiogram import Dispatcher
from typing import Any, Dict

from .middleware.session_timeout import SessionTimeoutMiddleware


async def setup_dependencies(dp: Dispatcher) -> None:
    dp["services"] = {}
    
    try:
        from bathhouse_booking.bookings import services
        dp["services"] = {
            "create_booking_request": services.create_booking_request,
            "report_payment": services.report_payment,
            "approve_booking": services.approve_booking,
            "reject_booking": services.reject_booking,
            "get_available_slots": services.get_available_slots,
            "cancel_booking": services.cancel_booking,
        }
    except ImportError:
        pass
    
    # Добавляем middleware для таймаута сессий
    dp.update.outer_middleware(SessionTimeoutMiddleware())


def get_services(dp: Dispatcher) -> Dict[str, Any]:
    services = dp.get("services")
    return services if services is not None else {}