# MixCut

AI-powered video mixing and editing platform. Upload raw clips, describe your goal in plain language, and receive a polished output video — refine with natural language until satisfied.

## Features

- **Multi-Agent Pipeline**: LangGraph-based orchestration with Understand → Plan → Execute → Subtitle → TTS → Review → Export nodes
- **Natural Language Editing**: Describe video goals in plain language; correct outputs with iterative feedback
- **Multi-Model Support**: Anthropic Claude, OpenAI GPT-4o, Google Gemini, DashScope Qwen3-VL/Qwen3, Ollama (any model)
- **Video Processing**: FFmpeg-powered trim, concat, resize, speed adjustment, text overlay, transitions
- **Subtitle & TTS**: Whisper transcription with LLM polish, MiniMax/Volcengine TTS dubbing
- **Real-time Progress**: SSE-based live job progress, agent trace logging
- **Observable**: OpenTelemetry tracing, Prometheus metrics, Jaeger integration, structlog JSON logging
- **Professional UI**: Next.js 15 + Tailwind CSS 4, custom video player, timeline editor, chat panel

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Next.js 15 Frontend                     │
│         TypeScript · Tailwind · TanStack Query           │
└────────────────────────┬────────────────────────────────┘
                         │ REST + SSE
┌────────────────────────▼────────────────────────────────┐
│                    FastAPI Backend                        │
│            API Gateway · Job Management                   │
├──────────────────────────────────────────────────────────┤
│                  Agent Harness Layer                      │
│     Retry · Timeout · Circuit Breaker · Validation       │
├──────────┬──────────────┬──────────────┬────────────────┤
│  Model   │  LangGraph   │   FFmpeg     │   Storage      │
│ Registry │  Multi-Agent │  Pipeline    │  Local / S3    │
└──────────┴──────────────┴──────────────┴────────────────┘
         │              │              │
┌────────▼──────────────▼──────────────▼─────────────────┐
│                    Infrastructure                        │
│    PostgreSQL · Redis · MinIO · Jaeger · Prometheus     │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS 4, TanStack Query, Zustand |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), asyncpg, Alembic |
| Agents | LangGraph, multi-model registry with fallback routing |
| Video | FFmpeg (trim, concat, resize, speed, overlay, subtitle burn, audio mix) |
| Transcription | Whisper large-v3 |
| TTS | MiniMax TTS, Volcengine TTS |
| Queue | Celery 5 + Redis |
| Database | PostgreSQL 16 |
| Storage | Local filesystem / S3-compatible (MinIO) |
| Observability | OpenTelemetry, Prometheus, Jaeger, structlog |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- FFmpeg

### 1. Start Infrastructure

```bash
cp .env.example .env
make infra-up
```

This starts PostgreSQL, Redis, MinIO, Jaeger, Prometheus, and Grafana.

| Service | URL |
|---------|-----|
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| MinIO API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |
| Jaeger UI | `http://localhost:16686` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3001` |

### 2. Backend

```bash
cd backend
pip install -e ".[dev]"
make backend-dev   # or: uvicorn backend.main:app --reload --port 8000
```

### 3. Worker

```bash
make worker-dev    # or: celery -A backend.workers.tasks worker --loglevel=INFO
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET/POST | `/api/v1/projects` | List / create projects |
| POST | `/api/v1/assets/project/{id}/upload` | Upload video/image |
| POST | `/api/v1/jobs` | Start a render job |
| GET | `/api/v1/jobs/{id}` | Get job status |
| GET | `/api/v1/jobs/{id}/stream` | SSE progress stream |
| POST | `/api/v1/jobs/{id}/resume` | Resume after human review |
| POST | `/api/v1/jobs/{id}/correct` | Submit correction |
| GET | `/api/v1/models` | List model providers |
| GET | `/api/v1/models/health` | Model health status |
| POST | `/api/v1/export` | Export final video |
| GET | `/metrics` | Prometheus metrics |

## Agent Pipeline

```
Upload → Understand (parallel per asset) → Plan → Execute
  → [Subtitle] → [TTS] → Human Review → Export
                                    ↓
                              Correct → Re-run affected nodes
```

Each node runs through the Agent Harness: retry with exponential backoff, per-node timeout, circuit breaker per model provider, and output schema validation.

## Project Structure

```
MixCut/
├── backend/
│   ├── api/            # FastAPI route handlers
│   ├── agent/          # LangGraph agents & nodes
│   │   ├── agents/     # Agent definitions (understand, plan, execute, etc.)
│   │   ├── nodes/      # Node implementations
│   │   └── prompts/    # LLM prompt templates
│   ├── harness/        # Agent reliability layer
│   ├── model/          # Multi-model provider registry
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic schemas
│   ├── tools/          # FFmpeg, Whisper, TTS, storage
│   ├── workers/        # Celery tasks
│   ├── observability/  # Logging, metrics, tracing
│   └── tests/          # Backend tests
├── frontend/
│   ├── app/            # Next.js App Router pages
│   ├── components/     # React components
│   │   ├── editor/     # Editor page components
│   │   ├── dashboard/  # Dashboard components
│   │   ├── layout/     # Shell, sidebar, topbar
│   │   └── ui/         # Design system primitives
│   ├── lib/            # API client, SSE, store, i18n
│   └── hooks/          # Custom React hooks
├── docker-compose.yml  # Local infrastructure
├── Makefile            # Developer commands
└── AGENTS.md           # Detailed architecture spec
```

## Development Commands

```bash
make infra-up          # Start Postgres, Redis, MinIO, Jaeger, Prometheus, Grafana
make infra-down        # Stop all services
make infra-logs        # Follow service logs
make infra-check       # Verify service endpoints
make backend-dev       # Run FastAPI with hot reload
make worker-dev        # Run Celery worker
make frontend-dev      # Run Next.js dev server
```

## Environment Variables

See [`.env.example`](.env.example) for all configuration options including:

- Model provider API keys (Anthropic, OpenAI, Google, DashScope, Ollama)
- Database and Redis connection strings
- Storage backend configuration (local / S3)
- TTS provider credentials (MiniMax, Volcengine)
- Agent harness tuning (timeouts, circuit breaker thresholds)
- Observability endpoints

## License

MIT
