import json

import redis

from app.config import settings


client = redis.from_url(settings.redis_url, decode_responses=True)


def ping() -> bool:
    return bool(client.ping())


def load_history(user_id: str) -> list[dict]:
    values = client.lrange(f"history:{user_id}", 0, -1)
    return [json.loads(value) for value in values]


def append_history(user_id: str, role: str, content: str) -> None:
    key = f"history:{user_id}"
    client.rpush(key, json.dumps({"role": role, "content": content}))
    client.ltrim(key, -settings.history_max_messages, -1)
    client.expire(key, settings.history_ttl_seconds)
