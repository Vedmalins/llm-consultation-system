from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


class BotTokenError(ValueError):
    pass


class BotTokenExpiredError(BotTokenError):
    pass


def decode_and_validate(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
        )
    except ExpiredSignatureError as exc:
        raise BotTokenExpiredError("Token expired") from exc
    except JWTError as exc:
        raise BotTokenError("Invalid token") from exc

    if not payload.get("sub"):
        raise BotTokenError("Token payload does not contain sub")

    if not payload.get("role"):
        raise BotTokenError("Token payload does not contain role")

    return payload