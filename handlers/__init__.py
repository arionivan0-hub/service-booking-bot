from aiogram import Router

from .menu import router as menu_router
from .registration import router as registration_router
from .services import router as services_router
from .booking import router as booking_router
from .my_appointments import router as my_appointments_router
from .contacts import router as contacts_router
from .admin import router as admin_router


def register_handlers(root: Router) -> None:
    root.include_router(admin_router)
    root.include_router(registration_router)
    root.include_router(menu_router)
    root.include_router(services_router)
    root.include_router(booking_router)
    root.include_router(my_appointments_router)
    root.include_router(contacts_router)
