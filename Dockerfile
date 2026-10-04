# Multi-stage production Dockerfile: Unified Full-Stack Architecture
# Stage 1: Build Next.js Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Production Unified Runner (FastAPI + Next.js Server via Reverse Proxy)
FROM python:3.11-slim AS runner
WORKDIR /app

# Install system dependencies & Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy frontend build artifacts
COPY --from=frontend-builder /app/frontend/package*.json ./frontend/
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public

EXPOSE 8000 3000 10000

ENV PORT=10000
ENV PYTHONUNBUFFERED=1

# Start script: Runs both FastAPI and Next.js, proxying requests seamlessly
COPY <<'EOF' /app/start.sh
#!/bin/bash
set -e

APP_PORT="${PORT:-10000}"

if [ "$SERVICE_TYPE" = "backend_only" ]; then
    echo "Starting FastAPI Backend only on port ${APP_PORT}..."
    exec uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port "${APP_PORT}"
elif [ "$SERVICE_TYPE" = "frontend_only" ]; then
    echo "Starting Next.js Frontend only on port ${APP_PORT}..."
    cd /app/frontend && exec npm start -- -p "${APP_PORT}"
else
    echo "Starting Full-Stack NexPath on port ${APP_PORT}..."
    # Start FastAPI Backend on internal port 8000
    uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    # Start Next.js Frontend on the Render dynamic PORT
    cd /app/frontend
    npm start -- -p "${APP_PORT}" &
    FRONTEND_PID=$!

    # Trap exit to shut down both cleanly
    trap "kill $BACKEND_PID $FRONTEND_PID" SIGINT SIGTERM EXIT
    wait
fi
EOF

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
