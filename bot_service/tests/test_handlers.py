from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import fakeredis.aioredis
import pytest
from jose import jwt

from app.bot.handlers import text_handler, token_handler, token_key
from app.core.config import settings


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeChat:
    def __init__(self, chat_id: int) -> None:
        self.id = chat_id


class FakeMessage:
    def __init__(self, text: str, user_id: int = 123, chat_id: int = 456) -> None:
        self.text = text
        self.from_user = FakeUser(user_id)
        self.chat = FakeChat(chat_id)
        self.answer = AsyncMock()


def create_test_token() -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": "1",
        "role": "user",
        "iat": int(now.timestamp()),
        "exp": now + timedelta(minutes=30),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


@pytest.mark.asyncio
async def test_token_handler_saves_token(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.bot.handlers.get_redis", lambda: fake_redis)

    token = create_test_token()
    message = FakeMessage(f"/token {token}", user_id=123)

    await token_handler(message)

    saved_token = await fake_redis.get(token_key(123))

    assert saved_token == token
    message.answer.assert_awaited_with("Токен принят и сохранён.")


@pytest.mark.asyncio
async def test_text_handler_without_token_denies_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.bot.handlers.get_redis", lambda: fake_redis)

    message = FakeMessage("What is API?", user_id=123)

    await text_handler(message)

    assert message.answer.await_count == 1
    assert "Доступ запрещён" in message.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_text_handler_with_token_sends_celery_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.bot.handlers.get_redis", lambda: fake_redis)

    task_mock = Mock()
    monkeypatch.setattr("app.bot.handlers.llm_request.apply_async", task_mock)

    token = create_test_token()
    await fake_redis.set(token_key(123), token)

    message = FakeMessage("What is API?", user_id=123, chat_id=456)

    await text_handler(message)

    task_mock.assert_called_once_with(args=[456, "What is API?"])
    message.answer.assert_awaited_with(
        "Запрос принят в обработку. Ответ придёт позже."
    )