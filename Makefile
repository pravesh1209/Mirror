# MIRROR Makefile

.PHONY: help install backend frontend dev-db up down test typecheck smoke clean db-reset

help:
@echo "make install    - install backend + frontend deps"
@echo "make backend    - run FastAPI on :8000"
@echo "make frontend   - run Next.js on :3000"
@echo "make dev-db     - start only Postgres via docker"
@echo "make up         - full docker compose up"
@echo "make down       - docker compose down"
@echo "make test       - run backend tests"
@echo "make typecheck  - run frontend tsc --noEmit"
@echo "make smoke      - run pre-pitch smoke test"
@echo "make db-reset   - delete and recreate the SQLite database"
@echo "make clean      - remove .db and caches"

install:
cd backend && python -m pip install -r requirements.txt
cd frontend && npm install

backend:
cd backend && python -m uvicorn app.main:app --reload --port 8000

frontend:
cd frontend && npm run dev

dev-db:
docker compose up -d db

up:
docker compose up --build

down:
docker compose down

test:
cd backend && python -m pytest -q

typecheck:
cd frontend && npx tsc --noEmit

smoke:
powershell -ExecutionPolicy Bypass -File scripts/smoke_test.ps1

db-reset:
-del /q backend\mirror.db 2>nul || true
cd backend && python -m app.db_init

clean:
-del /q backend\mirror.db 2>nul || true
-rmdir /s /q backend\.pytest_cache 2>nul || true
-rmdir /s /q frontend\.next 2>nul || true