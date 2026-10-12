#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
(cd backend && python -m uvicorn app.main:app --reload --port 8000) &
(cd frontend && npm install && npm run dev -- --host 0.0.0.0) &
wait
