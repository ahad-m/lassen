# AGENTS.md

## Cursor Cloud specific instructions

### Project overview
Lasan (لَسِن) is a full-stack Arabic poetry web app: React/TypeScript frontend (Vite, port 8080) + Python FastAPI backend (port 8000). See `README.md` for full architecture.

### Services

| Service | Start command | Port | Notes |
|---------|--------------|------|-------|
| Frontend | `npm run dev` (from repo root) | 8080 | Vite dev server with HMR |
| Backend | `cd Backend && source venv/bin/activate && uvicorn main:app --reload --port 8000` | 8000 | FastAPI; requires Python 3.11 venv |

### Backend Python environment
- The backend **must** use Python 3.11 (installed via `deadsnakes` PPA as `python3.11`).
- The venv lives at `Backend/venv/` and is created with `python3.11 -m venv venv`.
- After activating the venv, install deps: `pip install -r Requirements.txt && pip install numpy requests supabase`.
- `Requirements.txt` only lists core deps (fastapi, uvicorn, openai, httpx, python-dotenv, pydantic); `numpy`, `requests`, and `supabase` are additional runtime deps needed by services.

### Frontend
- Standard commands: `npm install`, `npm run dev`, `npm run build`, `npm run test`, `npm run lint`.
- Lockfile is `package-lock.json` (use `npm`).
- Existing lint warnings/errors are pre-existing in shadcn/ui generated components — not caused by new changes.

### Frontend → Backend connection
- `src/services/api.ts` has `BASE` hardcoded to the production Render URL by default.
- For local development, change `const BASE` to `"http://localhost:8000"` in `api.ts`.

### External API keys (required for full functionality)
The backend needs these env vars (set in `Backend/.env`):
- `OPENAI_API_KEY` — required for most features (mood, generation, interpretation, word explanation)
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` — required for poetry database queries
- `FASSERHA_REMOTE_URL` + `FASSERHA_REMOTE_API_KEY` — required for Poetry Interpretation classifiers
- Optional: `ELEVENLABS_API_KEY`, `TAVILY_API_KEY`, `SIWAR_API_KEY`

Without these keys, the backend starts successfully but API endpoints that depend on them return errors.

### Running tests
- Frontend: `npm run test` (Vitest, jsdom environment)
- No backend test suite exists in the repository.

### Gotchas
- The `Backend/venv/` directory is tracked in git (from the original repo). After recreating it with Python 3.11, `git status` will show many changes under `Backend/venv/` — these should not be committed.
- Prompt template files (e.g., `MoodOfTheDay_promts.py`) live directly in `Backend/`, not in a `Prompts/` subdirectory (despite the README's project structure diagram).
- The backend's `poetry_retriever.py`, `verse_searcher.py`, and `poetry_game_service.py` all require Supabase credentials at runtime.
