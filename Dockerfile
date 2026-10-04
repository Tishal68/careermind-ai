# Multi-stage production Dockerfile: Unified Full-Stack Architecture
# Stage 1: Build Next.js Static Web Application
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Production Unified Runner (FastAPI serving Website & API)
FROM python:3.11-slim AS runner
WORKDIR /app

# Install system dependencies for document parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy compiled Next.js static website files into /app/frontend/out
COPY --from=frontend-builder /app/frontend/out ./frontend/out

EXPOSE 8000 10000

ENV PORT=10000
ENV PYTHONUNBUFFERED=1

# Start script: Serves both the Web UI and the API on Render's dynamic $PORT
COPY <<'EOF' /app/start.sh
#!/bin/sh
set -e
APP_PORT="${PORT:-10000}"
echo "Starting NexPath Unified Engine on port ${APP_PORT}..."
exec python -m uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port "${APP_PORT}"
EOF

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
