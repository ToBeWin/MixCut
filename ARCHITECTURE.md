# MixCut Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Browser / Next.js 15 Client                   │
│              TypeScript · Tailwind CSS · TanStack Query           │
│                                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Dashboard │ │  Editor  │ │  Upload  │ │    Settings      │  │
│  │   Page    │ │   Page   │ │   Page   │ │     Page         │  │
│  └─────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘  │
│        │            │            │                │              │
│  ┌─────▼────────────▼────────────▼────────────────▼──────────┐  │
│  │              lib/api.ts · lib/sse.ts · lib/store.ts      │  │
│  └─────────────────────┬───────────────────────────────────┘  │
└────────────────────────┬───────────────────────────────────────┘
                         │ REST API + SSE
┌────────────────────────▼───────────────────────────────────────┐
│                      FastAPI Backend                            │
│                                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐   │
│  │ Projects │ │  Assets  │ │   Jobs   │ │  Chat/Correct  │   │
│  │  CRUD    │ │ Upload   │ │ Lifecycle│ │   + Resume     │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬─────────┘   │
│       │            │            │               │              │
│  ┌────▼────────────▼────────────▼───────────────▼──────────┐   │
│  │              SQLAlchemy ORM · asyncpg                    │   │
│  └────────────────────────┬───────────────────────────────┘   │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────────┐   │
│  │                  Agent Harness Layer                     │   │
│  │  Loop Control · Retry · Timeout · Circuit Breaker       │   │
│  │  Output Validation · Observability · Checkpointing       │   │
│  └────────────────────────┬───────────────────────────────┘   │
│                           │                                     │
│  ┌──────────┐  ┌─────────▼─────────┐  ┌──────────────────┐    │
│  │  Model   │  │   Specialist      │  │    FFmpeg +      │    │
│  │ Registry │  │     Agents        │  │   Tool Pipeline   │    │
│  │          │  │                   │  │                   │    │
│  │ ┌──────┐ │  │ ┌───────────────┐ │  │ ┌───────────────┐ │    │
│  │ │Mock  │ │  │ │ Understand    │ │  │ │ probe (ffprobe)│ │    │
│  │ │Anth. │ │  │ │ Plan          │ │  │ │ trim/concat   │ │    │
│  │ │OpenAI│ │  │ │ Execute       │ │  │ │ resize/speed  │ │    │
│  │ │Google│ │  │ │ Subtitle      │ │  │ │ keyframe ext  │ │    │
│  │ │DashSc│ │  │ │ TTS           │ │  │ │ whisper trans  │ │    │
│  │ │Ollama│ │  │ │ Correct       │ │  │ │ audio mix/norm │ │    │
│  │ └──────┘ │  │ └───────────────┘ │  │ └───────────────┘ │    │
│  └──────────┘  └─────────────────┘  └──────────────────┘    │
│                                                                │
│  ┌──────────┐  ┌─────────┐  ┌───────────┐  ┌──────────────┐   │
│  │ Storage  │  │ Check-  │  │ Workers   │  │ Observability│   │
│  │ Backend  │  │ pointer │  │ (Celery)  │  │ OTel+Prom    │   │
│  │Local/S3  │  │File/DB  │  │ Progress  │  │ structlog    │   │
│  └──────────┘  └─────────┘  └───────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
┌────────▼──────────────▼──────────────▼──────────────▼─────────┐
│                       Infrastructure                            │
│                                                                │
│  ┌──────────┐  ┌─────────┐  ┌─────────┐  ┌────────────────┐   │
│  │PostgreSQL│  │  Redis  │  │ MinIO  │  │ Jaeger+Grafana │   │
│  │    16    │  │   7     │  │  S3    │  │   Tracing+Mon  │   │
│  └──────────┘  └─────────┘  └─────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Graph Topology

```
                         ┌─────────┐
                         │  START  │
                         └────┬────┘
                              │
                  ┌───────────▼───────────┐
                  │   Supervisor Agent     │
                  │  (route & orchestrate)  │
                  └───────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────▼────────┐    │    ┌──────────▼─────────┐
    │  Understand Agent  │    │    │  Correct Agent      │
    │  (vision: Qwen3-VL│    │    │  (intent parsing)  │
    │   Gemini · Ollama) │    │    │  (text: Claude ·   │
    └─────────┬─────────┘    │    │   GPT-4o · Qwen3) │
              │               │    └──────────┬──────────┘
              │               │               │
    ┌─────────▼─────────┐    │    ┌──────────▼─────────┐
    │   Plan Agent      │◄───┘    │   Human Review     │
    │  (edit script:    │         │   (await user       │
    │   Claude · GPT-4o │         │    approval)       │
    │   Qwen3)          │         └──────────┬──────────┘
    └─────────┬─────────┘                    │
              │              ┌──────────────┘
              │              │  approved → END
              │              │  correction → Correct Agent
    ┌─────────▼─────────┐  │
    │   Execute Agent    │  │
    │  (FFmpeg pipeline: │  │
    │   trim → speed →   │  │
    │   resize → overlay  │  │
    │   → concat)         │  │
    └─────────┬─────────┘  │
              │              │
       ┌──────┴──────┐      │
       │             │      │
┌──────▼──────┐ ┌───▼─────┐│
│  Subtitle   │ │   TTS   ││
│   Agent     │ │  Agent   ││
│ (Whisper →  │ │(MiniMax/││
│  LLM polish │ │ Volcengine│
│  ASS burn)  │ │  TTS)    ││
└──────┬──────┘ └───┬─────┘│
       │             │      │
       └──────┬──────┘      │
              │             │
         ┌────▼────┐        │
         │  Export │        │
         │ (final  │        │
         │  render)│        │
         └────┬────┘        │
              │              │
         ┌────▼────┐        │
         │   END   │        │
         └─────────┘        │
```

## Data Flow: Upload → Edit → Export

```
User uploads video
        │
        ▼
┌────────────────┐     ffprobe      ┌──────────────┐
│  Asset Upload   │──────────────────│  VideoProbe   │
│  (multipart)   │                  │  (metadata)   │
└───────┬────────┘                  └──────────────┘
        │
        ├──► Storage: assets/{project_id}/{asset_id}.mp4
        ├──► Storage: keyframes/{asset_id}/frame_XXXX.jpg
        ├──► Storage: proxies/{asset_id}_240p.mp4
        ├──► Storage: assets/{project_id}/{asset_id}_poster.jpg
        │
        ▼
┌────────────────┐     Model Call     ┌──────────────┐
│  Understand     │───────────────────►│  Qwen3-VL    │
│  Node           │◄──────────────────│  / Gemini     │
└───────┬────────┘                   └──────────────┘
        │ ClipMetadata per asset
        ▼
┌────────────────┐     Model Call     ┌──────────────┐
│  Plan Node      │───────────────────►│  Claude       │
│                 │◄──────────────────│  / GPT-4o     │
└───────┬────────┘                   └──────────────┘
        │ EditScript (segments, transitions, overlays)
        ▼
┌────────────────┐     FFmpeg          ┌──────────────┐
│  Execute Node   │───────────────────►│  trim → speed │
│                 │                    │  → resize →   │
│                 │                    │  text_overlay  │
│                 │                    │  → concat      │
└───────┬────────┘                   └──────────────┘
        │ draft_video.mp4
        ▼
┌────────────────┐     Whisper + ASS   ┌──────────────┐
│  Subtitle Node  │───────────────────►│  Whisper     │
│  (conditional)  │                    │  ASS burn-in  │
└───────┬────────┘                   └──────────────┘
        │
        ▼
┌────────────────┐     TTS API         ┌──────────────┐
│  TTS Node       │───────────────────►│  MiniMax     │
│  (conditional)  │                    │  / Volcengine │
└───────┬────────┘                   └──────────────┘
        │
        ▼
┌────────────────┐
│  Human Review   │──── user approves ───► Export ───► Download
│  (SSE stream)   │
└───────┬────────┘
        │ user corrects
        ▼
┌────────────────┐
│  Correct Agent  │────► parses intent ───► partial re-run
└────────────────┘
```

## Tech Stack Summary

| Layer | Technology |
|-------|-------------|
| **Frontend** | Next.js 15, React 19, TypeScript (strict), Tailwind CSS 4, TanStack Query v5, Zustand, Lucide |
| **API** | FastAPI, Pydantic v2 (strict), SQLAlchemy 2.0 async, asyncpg |
| **Agents** | LangGraph-style graph, Model Registry with fallback routing |
| **Models** | Anthropic Claude, OpenAI GPT-4o, Google Gemini, DashScope Qwen3-VL/Qwen3, Ollama (any model) |
| **Video** | FFmpeg (trim, concat, resize, speed, fade, overlay, subtitle burn, audio mix) |
| **Transcription** | Whisper large-v3 (Chinese + multilingual) |
| **TTS** | MiniMax TTS, Volcengine TTS |
| **Task Queue** | Celery 5 + Redis |
| **Database** | PostgreSQL 16, Alembic migrations |
| **Storage** | Local filesystem / S3-compatible (MinIO) |
| **Observability** | OpenTelemetry, Prometheus, Jaeger, structlog (JSON) |
| **Container** | Docker Compose (postgres, redis, minio, jaeger, prometheus, grafana) |