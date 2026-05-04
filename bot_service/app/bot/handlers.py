from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.jwt import BotTokenError, decode_and_validate
from app.infra.redis import get_redis
from app.tasks.llm_tasks import llm_request


router = Router()


def token_key(tg_user_id: int) -> str:
    return f"token:{tg_user_id}"


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! Чтобы пользоваться LLM-консультацией, сначала получи JWT "
        "в Auth Service, затем отправь команду:\n\n/token <jwt>"
    )


@router.message(Command("token"))
async def token_handler(message: Message) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя Telegram.")
        return

    parts = (message.text or "").split(maxsplit=1)

    if len(parts) != 2:
        await message.answer("Используй формат: /token <jwt>")
        return

    token = parts[1].strip()

    try:
        decode_and_validate(token)
    except BotTokenError:
        await message.answer(
            "Токен неверный или истёк. Получи новый токен в Auth Service."
        )
        return

    redis = get_redis()
    await redis.set(token_key(message.from_user.id), token)

    await message.answer("Токен принят и сохранён.")


@router.message()
async def text_handler(message: Message) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя Telegram.")
        return

    if not message.text:
        await message.answer("Отправь текстовый запрос.")
        return

    redis = get_redis()
    token = await redis.get(token_key(message.from_user.id))

    if not token:
        await message.answer(
            "Доступ запрещён. Сначала авторизуйся через Auth Service "
            "и отправь команду /token <jwt>."
        )
        return

    try:
        decode_and_validate(token)
    except BotTokenError:
        await message.answer(
            "Токен неверный или истёк. Получи новый токен в Auth Service."
        )
        return

    llm_request.apply_async(args=[message.chat.id, message.text])

    await message.answer("Запрос принят в обработку. Ответ придёт позже.")