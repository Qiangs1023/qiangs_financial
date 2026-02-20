FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir pip -U && \
    pip install --no-cache-dir .

COPY . .

RUN cp config.example.yaml config.yaml 2>/dev/null || true

ENV PYTHONUNBUFFERED=1
ENV FINPULSE_CONFIG=/app/config.yaml

CMD ["finpulse", "monitor"]
