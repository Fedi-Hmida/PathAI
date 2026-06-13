# PathAI

PathAI is a personalized learning path generator powered by LangGraph multi-agent orchestration, curated RAG, structured LLM outputs, adaptive assessment, curriculum generation, and progress tracking.

## Current Status

Phase 0 - Repository & Environment Foundation is being implemented.

This phase intentionally does not initialize Git, create branches, or add CI workflow files. Repository setup will be handled later.

## Monorepo Layout

```text
PathAI/
  backend/    FastAPI backend and AI orchestration services
  frontend/   Next.js frontend application
  rag/        Resource curation assets, schemas, and retrieval evaluation data
  docs/       Architecture, development, security, and planning documents
  scripts/    Local automation scripts
  infra/      Docker and deployment support files
  tests/      Cross-application and end-to-end tests
  Doc/        Project specification and planning documents
```

## Backend Quick Start

The `make` shortcuts use the root `Makefile` when GNU Make is available. On Windows, this repo also includes `make.cmd` as a fallback. In PowerShell without GNU Make, use `.\make.cmd api` or `.\make.cmd web`; in Command Prompt, `make api` and `make web` work from the project root.

From the project root, you can start the backend with:

```powershell
make api
```

By default this starts FastAPI at `http://127.0.0.1:8000`. You can override the port:

```powershell
make api API_PORT=8010
```

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Health endpoints:

- `GET http://localhost:8000/api/v1/health`
- `GET http://localhost:8000/api/v1/ready`

## Frontend Quick Start

From the project root, you can start the frontend with:

```powershell
make web
```

By default this starts Next.js at `http://localhost:3000`. You can override the port:

```powershell
make web WEB_PORT=3001
```

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

## Docker Skeleton

```powershell
Copy-Item backend/.env.example backend/.env
docker compose up --build
```

The Docker skeleton includes:

- FastAPI API container
- MongoDB container for local development
- ChromaDB container for local vector search development

## Phase 0 Deliverables

- Professional monorepo structure
- Backend FastAPI skeleton
- Health/readiness endpoints
- Settings and logging foundation
- Backend dependency and tooling files
- Frontend Next.js shell
- RAG resource folders and schema placeholder
- Docker Compose skeleton
- Development documentation
