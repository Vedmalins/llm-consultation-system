from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_returns_hash_not_plain_password() -> None:
    password = "12345678"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_create_access_token_contains_required_payload() -> None:
    token = create_access_token(subject="1", role="user")

    payload = decode_token(token)

    assert payload["sub"] == "1"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload