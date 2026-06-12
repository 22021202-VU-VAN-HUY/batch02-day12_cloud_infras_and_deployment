# Deployment Information

## Public URL
https://day12-ai-agent-production-1c0f.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```powershell
Invoke-RestMethod "https://day12-ai-agent-production-1c0f.up.railway.app/health"
```

Expected: JSON with `"status": "ok"`.

### Agent Test
```powershell
$body = @{ question = "Hello from Railway" } | ConvertTo-Json
Invoke-RestMethod `
  "https://day12-ai-agent-production-1c0f.up.railway.app/ask" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Expected: JSON answer from the mock agent.

## Environment Variables Set
Railway injects `PORT` automatically.

For the final `06-lab-complete` production agent, set these before deploying that folder:
- `AGENT_API_KEY`
- `REDIS_URL`
- `RATE_LIMIT_PER_MINUTE`
- `MONTHLY_BUDGET_USD`
- `LOG_LEVEL`

## Notes
The current public Railway deployment is the Part 3 Railway app. The final production-ready stack in `06-lab-complete` was validated locally with Docker Compose and Redis. To deploy the final stack, add a managed Redis service and set `REDIS_URL` on Railway or Render.
