import json
import logging
import signal
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_and_record_cost
from app.rate_limiter import check_rate_limit
from app.redis_client import append_history, load_history, ping
from utils.mock_llm import ask as llm_ask


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='{"ts":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
INSTANCE_ID = f"agent-{uuid.uuid4().hex[:8]}"
is_ready = False


class AskRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    question: str = Field(..., min_length=1, max_length=2000)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global is_ready
    ping()
    is_ready = True
    logger.info(json.dumps({"event": "startup", "instance": INSTANCE_ID}))
    yield
    is_ready = False
    logger.info(json.dumps({"event": "shutdown", "instance": INSTANCE_ID}))


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    started = time.time()
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    if "server" in response.headers:
        del response.headers["server"]
    logger.info(json.dumps({
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": round((time.time() - started) * 1000, 1),
        "instance": INSTANCE_ID,
    }))
    return response


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "instance": INSTANCE_ID,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "instance": INSTANCE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    if not is_ready:
        raise HTTPException(status_code=503, detail="Agent is not ready")
    try:
        redis_ready = ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Redis is unavailable") from exc
    return {"ready": redis_ready, "instance": INSTANCE_ID}


@app.post("/ask")
def ask_agent(body: AskRequest, api_identity: str = Depends(verify_api_key)):
    quota_id = f"{api_identity}:{body.user_id}"
    rate = check_rate_limit(quota_id)

    estimated_input_tokens = max(1, len(body.question.split()) * 2)
    estimated_cost = (
        estimated_input_tokens / 1000 * settings.input_cost_per_1k_tokens
        + settings.estimated_output_tokens / 1000 * settings.output_cost_per_1k_tokens
    )
    budget = check_and_record_cost(quota_id, estimated_cost)

    history = load_history(body.user_id)
    append_history(body.user_id, "user", body.question)
    answer = llm_ask(body.question)
    append_history(body.user_id, "assistant", answer)

    return {
        "user_id": body.user_id,
        "question": body.question,
        "answer": answer,
        "history_messages_before": len(history),
        "served_by": INSTANCE_ID,
        "rate_limit": rate,
        "budget": budget,
    }


@app.get("/history/{user_id}")
def history(user_id: str, _identity: str = Depends(verify_api_key)):
    return {"user_id": user_id, "messages": load_history(user_id)}


def handle_sigterm(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))


signal.signal(signal.SIGTERM, handle_sigterm)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
