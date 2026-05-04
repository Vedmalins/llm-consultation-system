import asyncio
import logging

from aiogram import Bot

from app.core.config import settings
from app.infra.celery_app import celery_app
from app.services.openrouter_client import OpenRouterError, call_openrouter


logger = logging.getLogger(__name__)


async def _process_llm_request(tg_chat_id: int, prompt: str) -> None:
    bot = Bot(token=settings.telegram_bot_token)

    try:
        answer = await call_openrouter(prompt)
    except OpenRouterError as exc:
        logger.exception("OpenRouter request failed")
        answer = f"Не удалось получить ответ от LLM: {exc}"
    except Exception:
        logger.exception("Unexpected LLM task error")
        answer = "Произошла непредвиденная ошибка при обработке запроса."

    await bot.send_message(chat_id=tg_chat_id, text=answer)
    await bot.session.close()


@celery_app.task(name="llm_request")
def llm_request(tg_chat_id: int, prompt: str) -> dict[str, str | int]:
    asyncio.run(_process_llm_request(tg_chat_id, prompt))

    return {
        "tg_chat_id": tg_chat_id,
        "status": "sent",
    }