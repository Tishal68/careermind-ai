# Multi-stage production Dockerfile: Unified Full-Stack Architecture
# Stage 1: Build Next.js Web Application
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Production Unified Runner (Next.js on $PORT + FastAPI on 8000)
FROM python:3.11-slim AS runner
WORKDIR /app

# Install system dependencies & Node.js for Next.js runtime
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

# Copy frontend build and node dependencies
COPY --from=frontend-builder /app/frontend/package*.json ./frontend/
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/next.config.js ./frontend/next.config.js

EXPOSE 8000 10000

ENV PORT=10000
ENV PYTHONUNBUFFERED=1

# Start script: Runs FastAPI on port 8000 and Next.js on Render's external $PORT
COPY <<'EOF' /app/start.sh
#!/bin/bash
set -e
APP_PORT="${PORT:-10000}"

echo "Starting FastAPI Backend on internal port 8000..."
uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Next.js Frontend on port ${APP_PORT}..."
cd /app/frontend
npm start -- -p "${APP_PORT}" &
FRONTEND_PID=$!

# Ensure both processes terminate cleanly on container shutdown
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" SIGINT SIGTERM EXIT
wait -n
EOF

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
