import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 0.5):
        self.limit = limit
        self.last_call: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        now = time.monotonic()

        if user_id in self.last_call:
            delta = now - self.last_call[user_id]
            if delta < self.limit:
                if isinstance(event, CallbackQuery):
                    await event.answer("Слишком часто, подождите.", show_alert=True)
                return None

        self.last_call[user_id] = now
        return await handler(event, data)
