import random
import time


RESPONSES = [
    "The production agent is running with Redis-backed state.",
    "This is a mock response; no external LLM key is required.",
    "Your request passed authentication, rate limiting, and budget checks.",
]


def ask(_question: str, delay: float = 0.05) -> str:
    time.sleep(delay)
    return random.choice(RESPONSES)
