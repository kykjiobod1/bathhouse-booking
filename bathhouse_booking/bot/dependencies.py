from aiogram import Dispatcher
from typing import Any, Dict


async def setup_dependencies(dp: Dispatcher) -> None:
    dp["services"] = {}
    
    try:
        from bookings import services
        dp["services"] = {
            "create_booking_request": services.create_booking_request,
            "report_payment": services.report_payment,
            "approve_booking": services.approve_booking,
            "reject_booking": services.reject_booking,
            "get_available_slots": services.get_available_slots,
        }
    except ImportError:
        pass


def get_services(dp: Dispatcher) -> Dict[str, Any]:
    services = dp.get("services")
    return services if services is not None else {}