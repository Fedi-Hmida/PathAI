SHELL := cmd.exe
.PHONY: help api web

help:
	@echo make api  - run the backend (uvicorn, loads root .env, http://localhost:8000)
	@echo make web  - run the frontend (npm run dev, http://localhost:3000)

api:
	cd backend && .venv\Scripts\python.exe scripts\run_dev.py

web:
	cd frontend && npm run dev
