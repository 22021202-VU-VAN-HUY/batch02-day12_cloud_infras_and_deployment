from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.redis_client import client


def _budget_key(user_id: str) -> str:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    return f"budget:{user_id}:{month}"


def check_and_record_cost(user_id: str, estimated_cost: float) -> dict:
    key = _budget_key(user_id)
    current = float(client.get(key) or 0)

    if current + estimated_cost > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "used_usd": round(current, 6),
                "budget_usd": settings.monthly_budget_usd,
            },
        )

    used = float(client.incrbyfloat(key, estimated_cost))
    client.expire(key, 32 * 24 * 60 * 60)
    return {
        "used_usd": round(used, 6),
        "remaining_usd": round(max(0, settings.monthly_budget_usd - used), 6),
    }
