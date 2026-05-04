import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_me_flow(client: AsyncClient) -> None:
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "ivanov@email.com",
            "password": "12345678",
        },
    )

    assert register_response.status_code == 201
    assert register_response.json()["email"] == "ivanov@email.com"
    assert "password_hash" not in register_response.json()

    login_response = await client.post(
        "/auth/login",
        data={
            "username": "ivanov@email.com",
            "password": "12345678",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    assert login_response.json()["token_type"] == "bearer"

    me_response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "ivanov@email.com"
    assert me_response.json()["role"] == "user"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    payload = {
        "email": "petrov@email.com",
        "password": "12345678",
    }

    first_response = await client.post("/auth/register", json=payload)
    second_response = await client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={
            "email": "sidorov@email.com",
            "password": "12345678",
        },
    )

    response = await client.post(
        "/auth/login",
        data={
            "username": "sidorov@email.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401