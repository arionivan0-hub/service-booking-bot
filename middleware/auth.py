from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from database.crud import get_user_by_telegram_id


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, CallbackQuery):
            user = event.from_user
        else:
            user = event.from_user

        if user is None:
            return await handler(event, data)

        db_user = await get_user_by_telegram_id(user.id)
        data["db_user"] = db_user
        return await handler(event, data)
