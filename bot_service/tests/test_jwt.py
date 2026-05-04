from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.jwt import BotTokenError, decode_and_validate


def create_test_token() -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": "1",
        "role": "user",
        "iat": int(now.timestamp()),
        "exp": now + timedelta(minutes=30),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def test_decode_and_validate_valid_token() -> None:
    token = create_test_token()

    payload = decode_and_validate(token)

    assert payload["sub"] == "1"
    assert payload["role"] == "user"


def test_decode_and_validate_invalid_token() -> None:
    with pytest.raises(BotTokenError):
        decode_and_validate("invalid-token")