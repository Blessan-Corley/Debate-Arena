# Debate Arena

A full-stack multi-agent AI debate app with live SSE streaming, live web-search status cards, Mongo-backed history, human interruptions, and a judge-driven ending.

## What It Does

- Host opens the debate once with a broadcast-style intro.
- Pro uses Groq for voice and Tavily for live web research.
- Con uses Gemini with Google Search grounding.
- Crowd reacts only when a point actually lands.
- Judge can interrupt for factual correction and decides when enough has been said.
- Every visible debate event is stored, including search activity, verdicts, and audience feedback.
- Previous debates can be reopened from the archive UI.

## Stack

### Backend

- FastAPI
- Server-Sent Events via `sse-starlette`
- Groq Python SDK
- Google Gen AI Python SDK
- Tavily Python SDK
- PyMongo async client

### Frontend

- React
- Vite
- Tailwind CSS
- Vitest for reducer tests

## Required APIs And Env Vars

You need these values:

- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `TAVILY_API_KEY`
- `MONGODB_URI`

Optional overrides:

- `MONGODB_DB_NAME`
- `MONGODB_STRICT_STARTUP`
- `MONGODB_TIMEOUT_MS`
- `CORS_ORIGINS`
- `GROQ_HOST_MODEL`
- `GROQ_PRO_MODEL`
- `GROQ_CROWD_MODEL`
- `GEMINI_CON_MODEL`
- `GEMINI_JUDGE_MODEL`
- `VITE_API_BASE_URL`

## Model Defaults

The code currently defaults to:

- Host: `llama-3.3-70b-versatile`
- Pro: `llama-3.3-70b-versatile`
- Crowd: `llama-3.3-70b-versatile`
- Con: `gemini-2.5-flash`
- Judge: `gemini-2.5-flash`

If you have paid Gemini capacity and want to experiment with a heavier judge, you can override `GEMINI_JUDGE_MODEL`, but the default is tuned for current free-tier friendliness and faster live verdicts.

## Local Setup

### 1. Backend

```bash
cd backend
py -3 -m pip install -r requirements.txt
copy .env.example .env
```

Fill in `.env`, then run:

```bash
py -3 -m uvicorn main:app --reload --port 8000
```

If you want to run it from the project root on Windows instead of changing directories, use:

```bash
start-backend.bat
```

### 2. Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

From the project root on Windows, you can also use:

```bash
start-frontend.bat
```

Open `http://localhost:5173`.

## MongoDB Storage

This project is built for Mongo deployment, not local SQLite.

The backend stores debates in Mongo with:

- debate metadata
- full visible event feed
- search-result metadata and sources
- verdict winner
- audience feedback

For deployment, use a MongoDB Atlas connection string in `MONGODB_URI`.

Mongo is now expected to be available. By default `MONGODB_STRICT_STARTUP=true`, and `backend.bat` runs a Mongo preflight before starting Uvicorn. If Atlas is unavailable, the backend should fail fast instead of starting in a mixed state.

## API Routes

- `GET /health`
- `GET /debate/history`
- `GET /debate/history/{debate_id}`
- `DELETE /debate/history/{debate_id}`
- `POST /debate/start`
- `POST /debate/interrupt`
- `POST /debate/feedback`

## Tests And Verification

### Backend

```bash
py -3 -m pytest backend/tests -q
```

### Frontend

```bash
cd frontend
npm exec vitest run
npm exec vite build
```

## Deployment

### Recommended

- Frontend: Vercel
- Backend: Render Web Service
- Database: MongoDB Atlas

### Frontend Deploy Notes

- Build command: `npm run build`
- Output directory: `dist`
- Set `VITE_API_BASE_URL` to your backend URL

### Backend Deploy Notes

- Install command: `py -3 -m pip install -r backend/requirements.txt`
- Start command: `cd backend && py -3 -m uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set all backend env vars from `backend/.env.example`

### Mongo Deploy Notes

- Create a MongoDB Atlas cluster
- Allow your backend IP or open access during hackathon testing
- Put the connection string into `MONGODB_URI`

## Current UI Features

- broadcast-style topic entry screen
- scrollable live debate feed
- live search status and source overlay
- single-shell arena layout with controlled transcript auto-scroll
- bottom control dock for interruptions
- collapsible archive rail with per-debate delete
- archive hamburger menu with refresh and collapse actions
- inline feedback after the verdict
- previous debate archive viewer
