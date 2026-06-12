# Day 12 Lab - Mission Answers

**Student Name:** Vũ Văn Huy

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded `OPENAI_API_KEY` and `DATABASE_URL`.
2. Fixed port `8000` instead of reading `PORT`.
3. Debug reload enabled in code.
4. No `/health` endpoint in the develop app.
5. Secrets are printed to logs.
6. App binds to `localhost`, which is not suitable inside containers/cloud.
7. No graceful shutdown or lifecycle cleanup.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcoded | Environment variables | Cloud platforms inject config through env vars. |
| Secrets | In source/logs | Required via env in production | Avoid leaking credentials in Git or logs. |
| Health check | Missing | `/health`, `/ready`, `/metrics` | Orchestrators need liveness/readiness signals. |
| Logging | `print()` | JSON structured logs | Easier to search and aggregate in production. |
| Shutdown | Abrupt | FastAPI lifespan + SIGTERM handler | Lets in-flight requests finish. |
| Bind address | `localhost` | `0.0.0.0` | Containers need to accept external traffic. |

### Test results
- Missing `AGENT_API_KEY` with `ENVIRONMENT=production`: failed fast as expected.
- Production endpoints tested: `/`, `/health`, `/ready`, `/metrics`, `/ask`.
- Server stopped after test; port `8000` was free.

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: develop uses `python:3.11`; production uses `python:3.11-slim`.
2. Working directory: `/app`.
3. `COPY requirements.txt` happens before app code to reuse Docker layer cache when only source code changes.
4. `CMD` supplies the default command and can be overridden; `ENTRYPOINT` defines the executable contract for the container.

### Exercise 2.3: Image size comparison
- Develop: `1.66 GB`
- Production multi-stage: `236 MB`
- Difference: about `86%` smaller.

### Exercise 2.4: Docker Compose stack
Services:
- `nginx`: public reverse proxy/load balancer on ports 80/443.
- `agent`: FastAPI service, internal port 8000.
- `redis`: session/cache/rate-limit backing service.
- `qdrant`: vector database placeholder for RAG.

Test results:
- `GET http://localhost/health`: `200 OK`
- `POST http://localhost/ask`: `200 OK`

Fix applied:
- Corrected compose build context for `02-docker/production`.
- Added missing `requirements.txt`.
- Adjusted Qdrant dependency so the stack is not blocked by an image-local curl healthcheck.

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- Platform: Railway.
- Project: `day12-ai-agent`.
- Public URL: https://day12-ai-agent-production-1c0f.up.railway.app

Test results:
- `/health`: `200 OK`
- `/ask`: `200 OK`
- Railway logs showed healthcheck success and Uvicorn running.

### Exercise 3.2: Render comparison
`railway.toml` is minimal and deployment-oriented: builder, start command, healthcheck path, restart policy.
`render.yaml` is a fuller blueprint: web service, region, plan, build/start commands, health check, env vars, and Redis add-on.

### Exercise 3.3: Cloud Run notes
`cloudbuild.yaml` describes CI/CD: test, build Docker image, push image, then deploy Cloud Run.
`service.yaml` defines runtime infrastructure: public ingress, min/max scale, concurrency, resources, env vars, secrets, liveness/startup probes.

## Part 4: API Security

### Exercise 4.1: API key authentication
- API key is checked by `verify_api_key`.
- Missing key returns `401`.
- Wrong key returns `403`.
- Rotate by changing `AGENT_API_KEY` in env/cloud variables and redeploying/restarting.

### Exercise 4.2: JWT authentication
Tested user: `student / demo123`.
- No token: `401`
- Token generated successfully.
- Authenticated `/ask`: `200`

### Exercise 4.3: Rate limiting
Algorithm: sliding window using timestamp deque.
Limits:
- User: 10 requests/minute.
- Admin: 100 requests/minute.
Admin bypass/upgrade is role-based: `teacher` gets the admin limiter.

Observed statuses after repeated requests:
`200,200,200,200,200,200,200,200,200,429,429,429`

### Exercise 4.4: Cost guard implementation
The advanced security demo uses a `CostGuard` class to track per-user and global daily spend and return `402` when a user budget is exceeded.
The final project implements Redis-backed monthly cost guard with keys like `budget:{user_id}:{YYYY-MM}` and TTL reset.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.2: Health and graceful shutdown
- Develop `/health`: `200 OK`
- Develop `/ready`: `200 OK`
- Server stopped cleanly and port `8000` was released.

### Exercise 5.3-5.5: Stateless design and load balancing
Production stack tested with 3 agent instances behind Nginx and Redis.

Results:
- Requests were served by three different instances.
- Conversation history preserved across instances via Redis.
- Test script reported: `Session history preserved across all instances via Redis`.

Fixes applied:
- Added missing production Dockerfile/requirements for Part 5.
- Fixed Docker runtime `PYTHONPATH`.
- Made the test script UTF-8 safe on Windows.

## Part 6: Final Project

### Implementation summary
Final project in `06-lab-complete` now includes:
- REST `/ask` endpoint.
- Redis-backed conversation history.
- Multi-stage Dockerfile.
- Environment-based config.
- API key authentication.
- Redis-backed sliding-window rate limiting.
- Redis-backed monthly cost guard.
- `/health` and `/ready`.
- SIGTERM handler and graceful Uvicorn shutdown timeout.
- Structured JSON logging.
- Nginx + Redis + scalable agent Compose stack.

### Validation
`python check_production_ready.py`:
- `20/20 checks passed`
- Result: `100%`

Final stack test results:
- `/health`: `200`
- `/ready`: `200`
- `/ask` without key: `401`
- `/ask` with key: `200`
- `/history/{user_id}` returned Redis-backed messages.
- Rate limiting returned `429` after the configured quota.
- Cost guard returned `402` with a low test budget.

### Railway Deployment (Lab Assignment)
- **Public API URL**: `https://day12-ai-agent-production-1c0f.up.railway.app`
- **Authentication**: Requires header `X-API-Key: vinai-day12-huy-2026-secure-key`
- **Endpoints Available**: `/`, `/health`, `/ready`, `/ask`, `/chat`
- **Status**: Successfully deployed using explicit Dockerfile builder. Redis is connected and functioning for stateless session history across deployment instances.
