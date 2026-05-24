# Opptra Pricing Intelligence

Opptra Pricing Intelligence is a pricing and decision-support system for SKU-level Buy Box monitoring, recommendation generation, override review, and portfolio-level insight synthesis.

The app is packaged as a single Docker service:
- FastAPI backend serves the API and the exported frontend assets.
- Next.js frontend is statically exported and copied into the backend image.
- SQLite stores queue runs, recommendations, and decisions.

## What it does

- Builds SKU recommendations from the pricing and competitor signals.
- Groups SKUs into actionable clusters for queue review.
- Supports human approval, snoozing, and overrides.
- Generates portfolio summary and synthesis views.
- Uses AI fallbacks when a primary provider is unavailable.

## Tech Stack

- Backend: Python 3.12, FastAPI, SQLite, uv
- Frontend: Next.js 14, React 18, Tailwind CSS
- AI providers: Anthropic, OpenAI, Google Gemini, optional Grok
- Runtime: Docker

## Local Development

### Backend

```powershell
cd backend
..\..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Environment Variables

Create a `.env` file at the project root with the keys below:

```env
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
XAI_API_KEY=

XAI_BASE_URL=https://api.x.ai/v1
XAI_MODEL=grok-2-latest

NEXT_PUBLIC_API_URL=http://localhost:8000
DATABASE_PATH=backend/data/decisions.db
```

Notes:
- `ANTHROPIC_API_KEY` powers the primary SKU recommendation and clustering paths.
- `OPENAI_API_KEY` powers the GPT-4o fallback path.
- `GOOGLE_API_KEY` powers portfolio synthesis.
- `XAI_API_KEY` powers the optional Grok fallback path.
- `DATABASE_PATH` should point to persistent storage in production.


## CI/CD

The repository includes a GitHub Actions workflow that:

- Checks the backend imports and Python bytecode compilation.
- Builds the frontend with Next.js.
- Builds the production Docker image on the main branch.

The workflow lives in `.github/workflows/ci.yml`.

## Project Layout

- `backend/` FastAPI app, services, data access, AI orchestration
- `frontend/` Next.js UI
- `docker-compose.yml` local single-service container setup
- `Dockerfile` production build for the combined app
