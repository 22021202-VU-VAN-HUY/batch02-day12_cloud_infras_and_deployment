FROM python:3.11-slim AS builder

WORKDIR /build
COPY 05-scaling-reliability/production/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runtime

RUN groupadd -r agent && useradd -r -g agent -d /app agent
WORKDIR /app
COPY --from=builder /root/.local /home/agent/.local
COPY 05-scaling-reliability/production/app.py .
COPY 05-scaling-reliability/production/utils/ ./utils/
RUN chown -R agent:agent /app

USER agent
ENV PATH=/home/agent/.local/bin:$PATH
ENV PYTHONPATH=/home/agent/.local/lib/python3.11/site-packages:/app
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
