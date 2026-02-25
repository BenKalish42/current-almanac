# Current Backend

FastAPI backend for the Current almanac application.

## Setup

```bash
# From project root
pip install -r backend/requirements.txt
```

## Run API

```bash
# From project root
npm run backend
# or
uvicorn backend.main:app --reload --port 8000
```

## Endpoints

- `GET /health` - Health check
- `POST /api/interpret` - Accept frontend payload, return DeepSeek interpretation
- `POST /api/chat` - Stream chat completions from DeepSeek (Zhuang)

## DeepSeek (AI)

Set `DEEPSEEK_API_KEY` (or `OPENAI_API_KEY`) for interpretation and chat:

```bash
export DEEPSEEK_API_KEY=sk-...   # Get at https://platform.deepseek.com/api_keys
```

Copy from `backend/.env.example` or add to a `.env` file in the backend directory.

## Phase 3: Database Initialization

### 1. Run Supabase migration

Execute the SQL in `supabase/migrations/20250224000001_create_herbs_formulas.sql` via the Supabase SQL Editor or CLI.

### 2. Load seed data

Set environment variables (copy from `backend/.env.example`):

```bash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_KEY=your-service-role-key
```

From project root:

```bash
python -m backend.init_db
```

This loads `src/data/seed_herbs.json` and `src/data/seed_formulas.json` into the `herbs`, `formulas`, and `formula_architecture` tables.

## Development

With the backend running on port 8000, the Vite dev server proxies `/api` to the backend. Generate a reading, then click "Generate AI Summary" to test the integration.
