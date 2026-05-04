import pytest
import respx
from httpx import Response

from app.core.config import settings
from app.services.openrouter_client import call_openrouter


@pytest.mark.asyncio
@respx.mock
async def test_call_openrouter_returns_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(settings, "openrouter_model", "openrouter/free")

    route = respx.post(
        f"{settings.openrouter_base_url}/chat/completions"
    ).mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Test LLM answer"
                        }
                    }
                ]
            },
        )
    )

    result = await call_openrouter("Hello")

    assert result == "Test LLM answer"
    assert route.called