from app.infra.celery_app import celery_app


@celery_app.task(name="llm_request")
def llm_request(tg_chat_id: int, prompt: str) -> dict[str, str | int]:
    return {
        "tg_chat_id": tg_chat_id,
        "prompt": prompt,
        "status": "accepted",
    }