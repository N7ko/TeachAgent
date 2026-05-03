#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
CONDA_ENV="${CONDA_ENV:-langchain}"
CONDA_SH="${CONDA_SH:-/opt/anaconda3/etc/profile.d/conda.sh}"

cd "$ROOT_DIR"
mkdir -p logs

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Fill DEEPSEEK_API_KEY before using DeepSeek."
fi

if [ ! -f "$CONDA_SH" ]; then
  echo "Cannot find conda init script: $CONDA_SH"
  echo "Set CONDA_SH=/path/to/conda.sh and rerun."
  exit 1
fi

if lsof -Pi ":$BACKEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Backend port $BACKEND_PORT is already in use. Stop that process or set BACKEND_PORT."
  exit 1
fi

if lsof -Pi ":$FRONTEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Frontend port $FRONTEND_PORT is already in use. Stop that process or set FRONTEND_PORT."
  exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm install)
fi

echo "Checking backend dependencies in conda env: $CONDA_ENV"
(
  source "$CONDA_SH"
  conda activate "$CONDA_ENV"
  python -c "import fastapi, langgraph, httpx, dotenv" >/dev/null 2>&1 || pip install -r requirements.txt
)

echo "Starting TeachAgent backend on http://127.0.0.1:$BACKEND_PORT"
(
  source "$CONDA_SH"
  conda activate "$CONDA_ENV"
  uvicorn main:app --host 127.0.0.1 --port "$BACKEND_PORT"
) > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > logs/backend.pid

echo "Starting TeachAgent frontend on http://127.0.0.1:$FRONTEND_PORT"
(
  cd frontend
  npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT"
) > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > logs/frontend.pid

cleanup() {
  echo
  echo "Stopping TeachAgent services..."
  kill "$BACKEND_PID" "$FRONTEND_PID" >/dev/null 2>&1 || true
  rm -f logs/backend.pid logs/frontend.pid
}

trap cleanup INT TERM EXIT

echo
echo "TeachAgent is running."
echo "Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "Backend:  http://127.0.0.1:$BACKEND_PORT"
echo "Logs:     logs/backend.log and logs/frontend.log"
echo
echo "Press Ctrl+C to stop both services."

wait
