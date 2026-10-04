# Multi-stage production Dockerfile supporting both Full-Stack (Default) and modular deployments
# Stage 1: Build Frontend Next.js
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Python Backend & Unified Runner
FROM python:3.11-slim AS runner
WORKDIR /app

# Install system dependencies & Node.js for Next.js runner
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

# Expose backend (8000) and frontend (3000) / Render default port
EXPOSE 8000 3000 10000

ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Start script
COPY <<'EOF' /app/start.sh
#!/bin/bash
if [ "$SERVICE_TYPE" = "frontend" ]; then
    echo "Starting Next.js Frontend on port ${PORT:-3000}..."
    cd /app/frontend && npm start -- -p ${PORT:-3000}
else
    echo "Starting FastAPI Backend on port ${PORT:-8000}..."
    cd /app/backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi
EOF

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
