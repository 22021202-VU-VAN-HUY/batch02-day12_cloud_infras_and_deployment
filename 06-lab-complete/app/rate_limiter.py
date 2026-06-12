import time
import uuid

from fastapi import HTTPException

from app.config import settings
from app.redis_client import client


def check_rate_limit(user_id: str) -> dict:
    now = time.time()
    key = f"rate:{user_id}"

    pipeline = client.pipeline()
    pipeline.zremrangebyscore(key, 0, now - 60)
    pipeline.zcard(key)
    _, count = pipeline.execute()

    if count >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )

    client.zadd(key, {f"{now}:{uuid.uuid4().hex}": now})
    client.expire(key, 61)
    return {
        "limit": settings.rate_limit_per_minute,
        "remaining": settings.rate_limit_per_minute - count - 1,
    }
