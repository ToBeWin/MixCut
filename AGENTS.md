# MixCut — AGENTS.md

AI-powered video mixing and editing platform.
Users upload raw video materials; a multi-Agent system understands content semantically,
plans edits based on user goals, executes via FFmpeg, supports subtitle and TTS dubbing,
and allows iterative natural language corrections throughout the process.

Design philosophy:
- Agent = Model + Harness. The model provides intelligence; the harness provides reliability.
- Premium UI: the interface feels like a professional creative tool, not a generic AI wrapper.
- Iterative by design: correction loops are first-class, not an afterthought.
- Model-agnostic: no lock-in to any single LLM or vision model.
- Observable: every agent step, model call, and FFmpeg command is traceable.

---

## Table of Contents

1. Product Vision
2. Architecture Overview
3. Tech Stack
4. Project Structure
5. Multi-Agent Design
6. Agent Harness — Core Principles
7. Model Layer — Multi-Model Support
8. LangGraph Graph Design
9. Key Data Schemas
10. API Design
11. Observability System
12. Frontend — UI Design System
13. Frontend — Page and Component Spec
14. Video Processing Pipeline
15. Natural Language Correction
16. Error Handling and Resilience
17. Storage and File Management
18. Infrastructure and Deployment
19. Environment Variables
20. Development Priorities
21. Code Standards

---

## 1. Product Vision

MixCut is a vertical AI Agent platform for video mixing and editing.

Core value proposition:
  Upload N raw clips → describe your goal in plain language → receive a polished output
  video → refine with natural language until satisfied.

Target users:
- E-commerce operators producing Douyin / Xiaohongshu / Taobao product videos
- MCN agencies needing batch video production at scale
- Short-form content creators (solo or small team)
- Corporate marketing teams (events, campaigns, tutorials)

Design principles:
- Agent = Model + Harness: model provides intelligence; harness provides reliability,
  looping, observability, and control flow.
- Premium UI: every interaction should feel intentional and refined.
- Iterative by design: the product is not a one-shot generator; correction loops are
  a first-class feature surfaced prominently in the UI.
- Model-agnostic: pluggable model layer with no lock-in to any single provider.
- Observable: every agent decision, model call, and FFmpeg command is logged, traced,
  and surfaced to the user in the UI.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser / Client                       │
│              Next.js 15 + TypeScript + Tailwind             │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST + SSE
┌──────────────────────────▼──────────────────────────────────┐
│                      FastAPI Backend                        │
│           API Gateway · Auth · Job Management               │
└──────┬───────────────────┬─────────────────┬────────────────┘
       │                   │                 │
┌──────▼──────┐   ┌────────▼────────┐  ┌────▼───────────────┐
│   Celery    │   │   LangGraph     │  │   PostgreSQL       │
│ Task Queue  │   │  Multi-Agent    │  │   + Redis          │
│  (Redis)    │   │  Orchestrator   │  │                    │
└──────┬──────┘   └────────┬────────┘  └────────────────────┘
       │                   │
┌──────▼───────────────────▼──────────────────────────────────┐
│                   Agent Harness Layer                       │
│      Loop Control · Retry · Timeout · Circuit Breaker       │
│      Output Validation · Observability · Checkpointing      │
└──────┬────────────────────┬───────────────┬─────────────────┘
       │                    │               │
┌──────▼──────┐   ┌─────────▼──────┐  ┌────▼───────────────┐
│ Model Layer │   │  FFmpeg Tools  │  │  Storage Layer     │
│ (Pluggable) │   │   Pipeline     │  │  Local / S3 OSS    │
│             │   │                │  │                    │
│ Claude      │   │ trim           │  │ assets/            │
│ GPT-4o      │   │ concat         │  │ keyframes/         │
│ Gemini      │   │ resize         │  │ proxies/           │
│ Qwen3-VL    │   │ overlay        │  │ temp/              │
│ Gemma4      │   │ subtitle       │  │ outputs/           │
│ Ollama(any) │   │ audio mix      │  │ tts/               │
└─────────────┘   └────────────────┘  └────────────────────┘
```

---

## 3. Tech Stack

### Backend

| Component            | Technology                         | Rationale                                      |
|----------------------|------------------------------------|------------------------------------------------|
| API Framework        | Python 3.11 + FastAPI              | Async-native, SSE streaming support            |
| Task Queue           | Celery 5 + Redis                   | Long-running video jobs, progress tracking     |
| Agent Orchestration  | LangGraph 0.2+                     | Stateful multi-agent graph, checkpointing      |
| ORM                  | SQLAlchemy 2.0 async               | Type-safe, async sessions                      |
| Migrations           | Alembic                            | Schema versioning                              |
| Validation           | Pydantic v2                        | All schemas, strict mode, model I/O contracts  |
| Video Processing     | FFmpeg via subprocess              | Industry standard, full programmatic control   |
| Video Understanding  | Qwen3-VL (primary)                 | Best Chinese e-commerce semantic understanding |
| Video Understanding  | Gemma4 27B (fallback / local)      | Apache 2.0, private deployment option          |
| Transcription        | OpenAI Whisper large-v3            | Chinese + multilingual, high accuracy          |
| TTS                  | MiniMax TTS / Volcengine TTS       | Chinese voice quality, stable APIs             |
| Observability        | OpenTelemetry + Jaeger             | Distributed tracing across all agents          |
| Logging              | structlog (JSON structured)        | Queryable, consistent log format               |
| Metrics              | Prometheus + Grafana               | Job throughput, model latency, error rates     |

### Frontend

| Component       | Technology                  | Rationale                                      |
|-----------------|-----------------------------|------------------------------------------------|
| Framework       | Next.js 15 (App Router)     | SSR, streaming, future Electron desktop port   |
| Language        | TypeScript strict            | No any, full type safety                       |
| Styling         | Tailwind CSS 4              | Utility-first, consistent design tokens        |
| UI Components   | Custom design system         | Premium look; no off-the-shelf kits            |
| Animation       | Framer Motion               | Page transitions, meaningful micro-interactions|
| Video Player    | Video.js with custom skin   | Reliable, fully skinnable                      |
| Global State    | Zustand                     | Lightweight, minimal boilerplate               |
| Server State    | TanStack Query v5           | Polling, caching, optimistic updates           |
| Icons           | Lucide React                | Consistent, lightweight                        |

### Infrastructure

| Component       | Technology                  |
|-----------------|-----------------------------|
| Container       | Docker + docker-compose     |
| Database        | PostgreSQL 16               |
| Cache / Broker  | Redis 7                     |
| Object Storage  | Local filesystem (dev) / S3-compatible OSS (prod) |
| Reverse Proxy   | Nginx                       |
| Process Monitor | Supervisor (Celery workers) |

---

## 4. Project Structure

```
mixcut/
├── backend/
│   ├── main.py                          # FastAPI app, lifespan hooks, middleware
│   ├── config.py                        # Pydantic Settings, all env vars
│   ├── deps.py                          # FastAPI dependency injection
│   │
│   ├── api/
│   │   ├── router.py                    # Mount all sub-routers
│   │   ├── projects.py                  # Project CRUD
│   │   ├── assets.py                    # Video asset upload and listing
│   │   ├── jobs.py                      # Job lifecycle + SSE progress stream
│   │   ├── chat.py                      # Natural language correction endpoint
│   │   ├── models.py                    # Available model listing + health
│   │   └── export.py                    # Final export + download
│   │
│   ├── agent/
│   │   ├── graph.py                     # LangGraph graph definition (entry point)
│   │   ├── state.py                     # AgentState TypedDict
│   │   ├── checkpointer.py              # PostgreSQL checkpointer setup
│   │   │
│   │   ├── agents/
│   │   │   ├── supervisor.py            # Supervisor Agent (top-level orchestrator)
│   │   │   ├── understand_agent.py      # Video Understanding Agent
│   │   │   ├── plan_agent.py            # Edit Planning Agent
│   │   │   ├── execute_agent.py         # Execution Agent (FFmpeg coordinator)
│   │   │   ├── subtitle_agent.py        # Subtitle Agent (Whisper + render)
│   │   │   ├── tts_agent.py             # TTS Dubbing Agent
│   │   │   └── correct_agent.py         # Correction Intent Agent
│   │   │
│   │   ├── nodes/
│   │   │   ├── understand.py            # LangGraph node: video understanding
│   │   │   ├── plan.py                  # LangGraph node: edit script planning
│   │   │   ├── execute.py               # LangGraph node: FFmpeg execution
│   │   │   ├── subtitle.py              # LangGraph node: subtitle pipeline
│   │   │   ├── tts.py                   # LangGraph node: TTS pipeline
│   │   │   ├── correct.py               # LangGraph node: correction + re-route
│   │   │   └── human_review.py          # LangGraph node: await user approval
│   │   │
│   │   └── prompts/
│   │       ├── understand.py            # Video understanding prompt templates
│   │       ├── plan.py                  # Edit script planning prompt templates
│   │       ├── correct.py               # Correction intent parsing prompts
│   │       └── tts_script.py            # Voiceover script generation prompts
│   │
│   ├── harness/
│   │   ├── loop.py                      # Agent loop controller (max_iterations, stop conditions)
│   │   ├── retry.py                     # Retry decorator with exponential backoff + jitter
│   │   ├── timeout.py                   # Per-node timeout enforcement
│   │   ├── circuit_breaker.py           # Circuit breaker for all external APIs
│   │   └── validator.py                 # Output schema validation between nodes
│   │
│   ├── model/
│   │   ├── base.py                      # ModelProvider abstract base class
│   │   ├── registry.py                  # Model registry + routing logic
│   │   ├── selector.py                  # Per-task model selection logic
│   │   └── providers/
│   │       ├── anthropic.py             # Claude (Sonnet / Opus)
│   │       ├── openai.py                # GPT-4o, GPT-4o-mini
│   │       ├── google.py                # Gemini 2.5 Flash / Pro
│   │       ├── qwen.py                  # Qwen3-VL + Qwen3 text via DashScope
│   │       ├── gemma.py                 # Gemma4 via Ollama or vLLM
│   │       └── ollama.py                # Generic Ollama provider (any local model)
│   │
│   ├── tools/
│   │   ├── ffmpeg/
│   │   │   ├── runner.py                # Sandboxed FFmpeg subprocess runner
│   │   │   ├── commands.py              # Typed command builders
│   │   │   ├── probe.py                 # ffprobe wrapper (video metadata)
│   │   │   └── errors.py               # FFmpegError, FFprobeError
│   │   ├── keyframe.py                  # Keyframe extraction utility
│   │   ├── whisper.py                   # Whisper transcription wrapper
│   │   ├── tts/
│   │   │   ├── base.py                  # TTSProvider abstract base
│   │   │   ├── minimax.py               # MiniMax TTS implementation
│   │   │   └── volcengine.py            # Volcengine TTS implementation
│   │   └── storage.py                   # Storage abstraction (local / S3)
│   │
│   ├── models/                          # SQLAlchemy ORM models
│   │   ├── project.py
│   │   ├── asset.py
│   │   ├── job.py
│   │   ├── edit_script.py               # JSONB column for EditScript
│   │   └── correction.py
│   │
│   ├── schemas/                         # Pydantic schemas (API I/O)
│   │   ├── project.py
│   │   ├── asset.py
│   │   ├── job.py
│   │   ├── clip_metadata.py
│   │   ├── edit_script.py
│   │   └── correction.py
│   │
│   ├── workers/
│   │   ├── tasks.py                     # Celery task definitions
│   │   └── progress.py                  # Progress event emitter (Redis pub/sub → SSE)
│   │
│   └── observability/
│       ├── tracing.py                   # OpenTelemetry tracer setup
│       ├── metrics.py                   # Prometheus metrics definitions
│       └── logging.py                   # structlog configuration
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                   # Root layout, fonts, theme providers
│   │   ├── page.tsx                     # Landing / marketing page
│   │   ├── dashboard/
│   │   │   └── page.tsx                 # Project dashboard
│   │   ├── project/
│   │   │   └── [id]/
│   │   │       ├── page.tsx             # Main editor page
│   │   │       ├── upload/page.tsx      # Asset upload flow
│   │   │       └── export/page.tsx      # Export and download
│   │   └── settings/
│   │       └── page.tsx                 # Model config, API keys, preferences
│   │
│   ├── components/
│   │   ├── ui/                          # Design system primitives
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Progress.tsx
│   │   │   ├── Tooltip.tsx
│   │   │   └── Toast.tsx
│   │   ├── editor/
│   │   │   ├── VideoPlayer.tsx          # Preview player with custom controls
│   │   │   ├── Timeline.tsx             # Visual edit script timeline
│   │   │   ├── AssetBrowser.tsx         # Source material panel
│   │   │   ├── SegmentCard.tsx          # Single segment in timeline
│   │   │   ├── ChatPanel.tsx            # Natural language correction chat
│   │   │   ├── AgentLog.tsx             # Live agent step trace (collapsible)
│   │   │   ├── ModelSelector.tsx        # Per-task model switcher
│   │   │   └── ExportPanel.tsx          # Export settings and download
│   │   ├── dashboard/
│   │   │   ├── ProjectCard.tsx
│   │   │   └── NewProjectModal.tsx
│   │   └── layout/
│   │       ├── Sidebar.tsx
│   │       ├── Header.tsx
│   │       └── StatusBar.tsx
│   │
│   ├── lib/
│   │   ├── api.ts                       # Typed API client (fetch wrappers)
│   │   ├── sse.ts                       # SSE hook for job progress streaming
│   │   └── store.ts                     # Zustand store definitions
│   │
│   └── styles/
│       ├── globals.css                  # CSS variables, base reset
│       └── tokens.css                   # Design tokens (colors, spacing, type)
│
├── docker-compose.yml                   # Local dev: postgres, redis, minio, jaeger
├── docker-compose.prod.yml              # Production overrides
├── nginx.conf
├── .env.example
└── AGENTS.md
```

---

## 5. Multi-Agent Design

MixCut uses a Supervisor + Specialist multi-agent architecture implemented in LangGraph.

### Agent Roles

**Supervisor Agent**
- Top-level orchestrator for the entire job
- Receives user goal and decides which specialist agents to invoke and in what order
- Monitors overall progress, handles inter-agent state passing
- Routes correction intents to the correct specialist for partial re-run
- Enforces global constraints: total duration, platform rules, quality gates
- Decides fallback behavior when a specialist agent fails

**Understand Agent**
- Transforms raw video files into structured semantic metadata
- Tools: keyframe extractor, Qwen3-VL / Gemma4 vision model
- Input: list of VideoAsset records
- Output: ClipMetadata per asset (scene, subjects, emotion, quality score, highlight segments)
- Runs in parallel across all assets using LangGraph fan-out / fan-in pattern
- Caches results; skips already-understood assets on re-run

**Plan Agent**
- Turns ClipMetadata and UserGoal into a concrete, time-coded EditScript
- Tools: text LLM (Claude / GPT-4o / Qwen3), platform rule reference
- Input: all ClipMetadata + UserGoal
- Output: EditScript JSON with ordered segments, timestamps, transitions, text overlays
- Includes planning rationale in output (why each clip was chosen)
- Can be re-invoked in isolation when the user requests a full re-plan

**Execute Agent**
- Translates EditScript into FFmpeg operations and produces a draft video
- Tools: FFmpeg command suite (trim, resize, concat, speed, overlay, audio mix)
- Input: EditScript + asset file paths
- Output: draft video file path
- Processes each segment independently; concatenates into draft

**Subtitle Agent**
- Transcription, text polishing, and subtitle rendering
- Tools: Whisper (transcription), text LLM (polishing), FFmpeg (ASS burn-in)
- Input: draft video path, optional user-provided script override
- Output: video with burned-in subtitles

**TTS Agent**
- Generates and mixes voiceover audio
- Tools: text LLM (voiceover script writing), TTS API (voice synthesis), FFmpeg (mix)
- Input: product copy from EditScript + draft video
- Output: video with mixed voiceover track and ducked background audio

**Correct Agent**
- Parses natural language corrections, determines affected agents, triggers selective re-run
- Tools: text LLM (intent parsing), EditScript diff utility
- Input: user correction message + current AgentState
- Output: updated AgentState + re-run plan (ordered list of agents to re-invoke)

### Agent Communication Pattern

```
User Goal
    │
    ▼
Supervisor Agent
    │
    ├──► Understand Agent ×N (parallel fan-out per asset)
    │         └──► fan-in: merged ClipMetadata[]
    │
    ├──► Plan Agent
    │         └──► EditScript
    │
    ├──► Execute Agent
    │         └──► draft_video.mp4
    │
    ├──► Subtitle Agent  (conditional on user goal)
    │
    ├──► TTS Agent  (conditional on user goal)
    │
    ▼
Human Review Node  (graph suspended, awaiting user input)
    │
    ├── approved ──► Export ──► END
    │
    └── correction ──► Correct Agent
                            └──► Supervisor Agent (partial re-run)
```

---

## 6. Agent Harness — Core Principles

The harness is the reliability and control layer that wraps every agent node.
It is entirely separate from model intelligence.

### 6.1 Loop Control

Every agent execution runs inside a managed loop:

- max_iterations: configurable per agent (default 10). Raises MaxIterationsExceeded
  if the agent has not produced valid output after N iterations.
- stop_conditions: a set of predicates evaluated after each iteration:
    - Output schema validates successfully against Pydantic model
    - Output passes semantic quality gate (e.g. edit script total duration within ±5s)
    - No pending correction intents
- loop_mode per agent:
    - single: one-shot, fail hard on invalid output
    - retry_on_invalid: loop with self-correction prompt until valid or max_iterations

### 6.2 Retry Strategy

Applied to every external call (model API, FFmpeg, TTS, Whisper):

- Exponential backoff: base 1s, multiplier 2x, max delay 60s
- Jitter: ±20% random jitter to prevent thundering herd on shared infrastructure
- Per-error-type policy:
    - 429 rate limit: always retry, respect Retry-After header
    - Timeout: retry up to 3 times
    - Schema / output validation failure: retry with self-correction prompt (max 3)
    - 401 / 403 auth error: fail immediately, surface clear error to user
    - FFmpeg non-zero exit: retry once with sanitized command;
      if fails again, mark segment as failed and continue with remaining segments

### 6.3 Timeout Enforcement

Each node has a configurable hard timeout. Breach raises NodeTimeoutError,
which the Supervisor handles by deciding to retry or degrade gracefully.

Default timeouts:

| Node                    | Default Timeout |
|-------------------------|-----------------|
| understand (per asset)  | 120s            |
| plan                    | 60s             |
| execute (per segment)   | 300s            |
| subtitle                | 180s            |
| tts                     | 120s            |
| correct                 | 30s             |

### 6.4 Circuit Breaker

Each external service (each model provider, each TTS provider) has its own circuit breaker:

- Closed (normal): calls pass through
- Open (failing): after N consecutive failures within a rolling window, the breaker opens.
  Calls immediately route to the fallback provider defined in the model registry.
- Half-open (recovering): after a cooldown period, one probe call is allowed.
  If it succeeds, the breaker closes. If not, cooldown resets.

Default thresholds: failure_threshold=5, recovery_timeout=60s (configurable via env).

### 6.5 Output Validation

Between every node, the output is validated before being passed downstream:

- Schema validation: Pydantic v2 strict mode against the node's output schema
- Semantic validation: custom validators per node
    - Segment in_point must be less than out_point
    - Total edit script duration within ±10% of target
    - All asset_ids in EditScript must exist in asset registry
    - TTS audio file must exist and be non-zero length
- On validation failure: node is re-invoked with a self-correction prompt that
  includes the full validation error message. Loop up to 3 times, then fail.

### 6.6 Human-in-the-Loop Node

human_review is a special LangGraph node that:
- Suspends the graph execution
- Persists full AgentState to PostgreSQL checkpointer
- Signals the frontend via SSE that user input is required
- Resumes when the user submits approval or a correction via the API
- Supports indefinite suspension (no timeout) — the graph lives in the DB

This is the mechanism for the iterative correction loop.

### 6.7 Partial Re-run

Node dependency map used by Correct Agent to determine re-run scope:

```
understand → plan → execute → subtitle
                         └──► tts
```

When a correction affects a node, that node and all downstream nodes are re-run.
Upstream nodes are skipped; their outputs are reused from state.node_outputs cache.

Partial re-run examples:
- Swap one clip → re-run execute + subtitle + tts (skip understand + plan)
- Change voiceover style → re-run tts only
- Change target duration → re-run plan + execute + subtitle + tts
- Full re-plan → re-run plan + execute + subtitle + tts

### 6.8 Self-Correction Loop

When a model produces output that fails schema or semantic validation:

1. Capture the full validation error message
2. Append it to the original prompt: "Your previous output was invalid. Error: {error}.
   Please fix only the invalid parts and return the corrected JSON."
3. Re-invoke the model
4. Repeat up to 3 times
5. If still invalid after 3 attempts: try fallback model provider
6. If fallback also fails: raise ModelOutputError, Supervisor handles graceful degradation

---

## 7. Model Layer — Multi-Model Support

The model layer is a fully pluggable abstraction. Any agent can use any model.
Choice is configurable per-project and overridable per-task in the UI.

### 7.1 ModelProvider Interface

Every provider implements the same interface:

```
ModelProvider
  properties:
    name: str
    supports_vision: bool
    context_window: int
    max_output_tokens: int

  methods:
    chat(messages, system, max_tokens, temperature) → str
    vision(messages, images_b64, system, max_tokens) → str
    stream_chat(messages, system) → AsyncIterator[str]
    health_check() → bool
```

Vision calls pass extracted keyframe images as base64-encoded content blocks.
All methods are async. All methods raise provider-specific exceptions that are
caught and normalized by the harness retry layer.

### 7.2 Supported Providers

| Provider     | Models                          | Vision Support | Primary Use Case                        |
|--------------|---------------------------------|----------------|-----------------------------------------|
| Anthropic    | claude-sonnet-4, claude-opus-4  | No             | Edit planning, intent parsing, copy     |
| OpenAI       | gpt-4o, gpt-4o-mini             | gpt-4o         | General fallback                        |
| Google       | gemini-2.5-flash, gemini-2.5-pro| Yes (video)    | Long video understanding, fallback VLM  |
| DashScope    | qwen3-vl, qwen3 (text)          | qwen3-vl       | Primary VLM; best Chinese e-commerce    |
| Ollama       | gemma4, llama3.3, qwen2.5-vl, * | model-dep.     | Local / private deployment, zero API cost|
| vLLM         | gemma4, qwen3-vl, *             | model-dep.     | High-throughput local inference         |

### 7.3 Model Registry — Default Task Routing

```
Task: video_understanding
  Primary:   qwen3-vl          (DashScope)
  Fallback1: gemma4:27b        (Ollama)
  Fallback2: gemini-2.5-flash  (Google)

Task: edit_planning
  Primary:   claude-sonnet-4   (Anthropic)
  Fallback1: gpt-4o            (OpenAI)
  Fallback2: qwen3             (DashScope)

Task: correction_intent
  Primary:   claude-sonnet-4   (Anthropic)
  Fallback1: gpt-4o-mini       (OpenAI)

Task: tts_script_writing
  Primary:   qwen3             (DashScope)  — best Chinese copy quality
  Fallback1: claude-sonnet-4   (Anthropic)
```

### 7.4 Ollama Integration Details

- Connect to OLLAMA_BASE_URL (default: http://localhost:11434)
- Use Ollama's OpenAI-compatible /v1/chat/completions endpoint
- Vision models: pass keyframes as base64 image content blocks
- Health check: GET /api/tags → verify model is loaded
- If model not loaded and OLLAMA_AUTO_PULL=true: run ollama pull {model} automatically
- Ollama models are listed dynamically in the UI model selector

### 7.5 Per-Project Model Configuration

Each project stores model preferences in the database.
Users can override defaults per-project in the Settings panel.
Available model list is fetched dynamically from all configured providers at startup.
Model health status (online / degraded / offline) is shown in the UI model selector.

---

## 8. LangGraph Graph Design

### 8.1 AgentState

```
AgentState (TypedDict)
  project_id: str
  job_id: str
  assets: List[VideoAsset]
  user_goal: UserGoal
    platform: str                  # douyin | xiaohongshu | taobao | bilibili | custom
    aspect_ratio: str              # 9:16 | 1:1 | 16:9
    style: str                     # lively | professional | storytelling | minimalist
    target_duration: int           # seconds
    selling_points: Optional[str]
    product_name: Optional[str]
    voiceover_requested: bool
    subtitle_requested: bool
    bgm_requested: bool
  clip_metadata: Dict[str, ClipMetadata]     # asset_id → ClipMetadata
  edit_script: Optional[EditScript]
  correction_history: List[CorrectionIntent]
  current_output_path: Optional[str]
  subtitle_path: Optional[str]
  node_outputs: Dict[str, Any]               # cached per-node output for partial re-run
  node_errors: Dict[str, List[str]]          # per-node error history
  iteration_count: Dict[str, int]            # per-node loop counter
  pending_human_input: bool
  final_output_path: Optional[str]
```

### 8.2 Graph Topology

```
START
  │
  ▼
supervisor_route
  │
  ├──► understand_node  (parallel fan-out ×N assets via Send API)
  │         └──► fan-in: all ClipMetadata merged into state
  │
  ▼
plan_node
  │
  ▼
execute_node
  │
  ├──► subtitle_node    (conditional: user_goal.subtitle_requested)
  ├──► tts_node         (conditional: user_goal.voiceover_requested)
  │
  ▼
human_review_node   ◄────────────────────────────────────────┐
  │                                                          │
  ├── approved ──► export_node ──► END                       │
  │                                                          │
  └── correction ──► correct_node ──► supervisor_route ──────┘
                                       (partial re-run)
```

### 8.3 Conditional Edge Logic

- supervisor_route → understand: always on first run; skip if all assets already have
  cached ClipMetadata in state.node_outputs
- execute → subtitle: only if user_goal.subtitle_requested is True
- execute → tts: only if user_goal.voiceover_requested is True
- subtitle and tts run concurrently when both are requested (LangGraph parallel branches)
- human_review → correct_node: triggered when pending_human_input is True and
  user has submitted a correction via the API
- correct_node → supervisor_route: always; supervisor reads CorrectionIntent.affected_nodes
  to determine which nodes to re-run vs skip (using cached node_outputs)

### 8.4 Checkpointing

LangGraph PostgreSQL checkpointer saves full AgentState after every node completes.

Enables:
- Resume after server restart or worker failure — no work is lost
- Time-travel debugging — inspect state at any past node boundary
- Full audit trail of all agent decisions for observability
- human_review suspension — state persists indefinitely until user resumes

---

## 9. Key Data Schemas

### UserGoal
```
platform: str                  # douyin | xiaohongshu | taobao | bilibili | custom
aspect_ratio: str              # 9:16 | 1:1 | 16:9
style: str                     # lively | professional | storytelling | minimalist
target_duration: int           # seconds
selling_points: Optional[str]
product_name: Optional[str]
target_audience: Optional[str]
voiceover_requested: bool
subtitle_requested: bool
bgm_requested: bool
```

### ClipMetadata
```
asset_id: str
filename: str
duration: float                # seconds
resolution: str                # e.g. "1920x1080"
fps: float
scene_description: str         # Chinese, ≤80 chars
subjects: List[str]            # people, products, props detected
emotion: str                   # positive | neutral | tense | warm | professional
camera_type: str               # close-up | medium | wide | extreme-close-up
action_tags: List[str]         # action verb phrases
quality_score: float           # 0.0–1.0 (composition + clarity + lighting)
highlight_segments: List
  start: float
  end: float
  reason: str
audio_present: bool
audio_description: Optional[str]
```

### EditScript
```
script_id: str
project_id: str
version: int                   # increments on each re-plan or correction
target_platform: str
target_duration: int
aspect_ratio: str
segments: List[Segment]
  segment_id: str
  asset_id: str
  in_point: float
  out_point: float
  transition_in: str           # cut | fade | dissolve | slide
  speed: float                 # 0.5–3.0
  volume: float                # 0.0–1.0 (original audio track)
  text_overlay: Optional
    text: str
    position: str              # top | bottom | center | top_left | bottom_right
    style: str                 # bold_white | outline_black | gradient | custom
    duration: Optional[float]  # seconds; null means full segment duration
bgm: Optional
  file: str
  volume: float
  fade_in: float
  fade_out: float
voiceover: Optional
  script: str
  voice_id: str
  speed: float
planning_rationale: str        # LLM explanation of editorial decisions (shown in AgentLog)
```

### CorrectionIntent
```
correction_id: str
raw_text: str                  # original user message, preserved verbatim
operations: List[Operation]
  type: str                    # see correction type table in section 15
  target: str                  # segment_id | "all" | "bgm" | "subtitle" | "tts"
  parameters: Dict             # operation-specific parameters
affected_nodes: List[str]      # nodes to re-run, in dependency order
parsed_at: datetime
```

### RenderJob
```
job_id: str
project_id: str
status: str                    # pending | running | paused | completed | failed
current_node: Optional[str]
progress: float                # 0.0–1.0
progress_message: str
agent_trace: List[TraceEvent]
created_at: datetime
started_at: Optional[datetime]
completed_at: Optional[datetime]
```

### TraceEvent (Observability)
```
event_id: str
job_id: str
node: str
agent: str
event_type: str                # node_start | node_complete | node_error |
                               # model_call | ffmpeg_call | retry | validation_fail
model_used: Optional[str]
prompt_tokens: Optional[int]
completion_tokens: Optional[int]
latency_ms: int
input_summary: str             # truncated, safe for display in UI
output_summary: str            # truncated, safe for display in UI
timestamp: datetime
```

---

## 10. API Design

All endpoints return JSON. Error responses follow RFC 7807 Problem Details format.
All routes are prefixed with /api/v1.

### Projects
```
POST   /projects                        Create new project
GET    /projects                        List projects (paginated, sorted by updated_at)
GET    /projects/{id}                   Get project detail
PATCH  /projects/{id}                   Update project metadata
DELETE /projects/{id}                   Delete project + all assets + all jobs
```

### Assets
```
POST   /projects/{id}/assets            Upload video asset (multipart/form-data)
GET    /projects/{id}/assets            List assets with metadata
DELETE /projects/{id}/assets/{aid}      Delete asset + keyframes + proxies
GET    /assets/{aid}/metadata           Get ClipMetadata for a specific asset
```

### Jobs
```
POST   /projects/{id}/jobs              Start agent run (body: UserGoal)
GET    /jobs/{job_id}                   Get job status + full trace
GET    /jobs/{job_id}/stream            SSE: live progress events (text/event-stream)
POST   /jobs/{job_id}/pause             Pause at next human_review node
POST   /jobs/{job_id}/resume            Resume from human_review (body: approved=true)
POST   /jobs/{job_id}/cancel            Cancel job and clean up temp files
```

### Correction
```
POST   /projects/{id}/correct           Submit natural language correction
                                        Resumes graph from human_review with correction
GET    /projects/{id}/corrections       List correction history (paginated)
```

### Preview and Export
```
GET    /projects/{id}/preview           Get current draft video URL
POST   /projects/{id}/export            Start final high-quality export render
GET    /projects/{id}/download          Download final video (redirect to storage URL)
```

### Models
```
GET    /models                          List all available models with health status
GET    /models/providers                List configured providers and their status
```

### SSE Event Schema
Each SSE event is a JSON object:
```
{
  "job_id": "uuid",
  "event_type": "progress | node_start | node_complete | node_error |
                 waiting_review | completed | failed",
  "node": "understand | plan | execute | subtitle | tts | correct | human_review",
  "progress": 0.65,
  "message": "Analyzing clip 3 of 7...",
  "trace_event": { TraceEvent object }
}
```

---

## 11. Observability System

Observability is first-class. Every agent step is traced, logged, and metricked.
The AgentLog UI component surfaces all of this directly to the user.

### 11.1 Distributed Tracing (OpenTelemetry + Jaeger)

- Every job creates a root span with job_id as the trace correlation ID
- Each LangGraph node creates a child span
- Each model call creates a nested span: provider, model, prompt token count,
  completion token count, latency ms
- Each FFmpeg command creates a nested span: command type, duration ms, exit code
- Each retry attempt creates a span event with reason
- Spans exported to Jaeger (dev) or any OTLP-compatible backend (prod)

### 11.2 Structured Logging (structlog)

All logs are JSON with consistent fields:
```json
{
  "timestamp": "2026-05-09T10:23:45.123Z",
  "level": "info",
  "job_id": "uuid",
  "node": "execute",
  "agent": "execute_agent",
  "event": "ffmpeg_command_complete",
  "command_type": "concat",
  "duration_ms": 4320,
  "trace_id": "abc123"
}
```

Log levels:
- DEBUG: full prompt text, full model responses, full FFmpeg commands
- INFO: node start/complete, model call summary, job status changes
- WARNING: retries, validation failures, circuit breaker state changes
- ERROR: node failures, unhandled exceptions

### 11.3 Prometheus Metrics

Exposed at GET /metrics:

| Metric                               | Type      | Labels                          |
|--------------------------------------|-----------|---------------------------------|
| mixcut_jobs_total                    | Counter   | status (completed, failed)      |
| mixcut_job_duration_seconds          | Histogram | —                               |
| mixcut_node_duration_seconds         | Histogram | node, agent                     |
| mixcut_model_call_duration_seconds   | Histogram | provider, model                 |
| mixcut_model_tokens_total            | Counter   | provider, model, type           |
| mixcut_ffmpeg_command_duration_seconds| Histogram| command_type                    |
| mixcut_ffmpeg_errors_total           | Counter   | command_type                    |
| mixcut_corrections_total             | Counter   | operation_type                  |
| mixcut_active_jobs                   | Gauge     | —                               |
| mixcut_circuit_breaker_state         | Gauge     | provider (0=closed, 1=open)     |

### 11.4 In-App AgentLog Component

The AgentLog component in the editor displays a live, collapsible trace of all
agent steps for the current job via SSE.

Each entry shows:
- Node name + agent name + status indicator (running / complete / error)
- Wall-clock duration
- Model used + token count (prompt + completion)
- Expandable: input summary and output summary
- Expandable: FFmpeg commands executed with duration
- Expandable: retry history if retries occurred

This gives users and developers full transparency into what the Agent decided
and why — critical for trust and for debugging incorrect edits.

---

## 12. Frontend — UI Design System

MixCut's UI must feel like a premium creative professional tool.
Reference quality bar: the craft of Linear, the density of Figma, the editorial
precision of a high-end studio product.

### 12.1 Design Direction

Aesthetic: refined dark-first professional tool. Deep neutral backgrounds,
sharp accent colors, precise typography. No rounded-off "friendly AI" look.
This is a tool for professionals who produce content at volume.

### 12.2 Color Palette

All colors defined as CSS custom properties. No hardcoded hex values in components.

```
--bg-primary:       #0C0C0E    near-black; main background
--bg-secondary:     #141416    panels, sidebars
--bg-elevated:      #1C1C20    cards, modals, popovers
--border:           #2A2A30    subtle dividers
--border-focus:     #6B5CFF    focused input outlines

--accent:           #6B5CFF    violet; primary actions, progress, highlights
--accent-hover:     #5A4CE0    darker violet on hover
--accent-teal:      #00C9A7    teal; AI activity, success states
--accent-teal-dim:  #00C9A722  transparent teal; AI activity backgrounds

--text-primary:     #F0EFE8    slightly warm white; headings, body
--text-secondary:   #8A8A94    muted; labels, metadata
--text-tertiary:    #52525C    disabled, placeholders

--danger:           #FF4D4F
--warning:          #FAAD14
--success:          #52C41A
```

### 12.3 Typography

- Display / headings: DM Sans (geometric, modern, clean at all weights)
- Body / UI labels: DM Sans (consistent with headings)
- Monospace (AgentLog, timestamps, technical data): JetBrains Mono
- Import via Google Fonts or self-host for privacy

Type scale:
```
--text-xs:   11px / 16px line-height
--text-sm:   13px / 18px
--text-base: 15px / 22px
--text-lg:   17px / 24px
--text-xl:   20px / 28px
--text-2xl:  24px / 32px
--text-3xl:  30px / 38px
```

### 12.4 Spacing, Radius, Shadow

Spacing: 4px base unit. Common: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64px
Border radius:
```
--radius-sm:  6px     inputs, badges, small elements
--radius-md:  10px    cards, modals (default)
--radius-lg:  16px    large panels
--radius-pill: 999px  status badges, tags
```
Shadows: dark-mode-tuned, minimal:
```
--shadow-sm:  0 1px 3px rgba(0,0,0,0.4)
--shadow-md:  0 4px 12px rgba(0,0,0,0.5)
--shadow-lg:  0 8px 32px rgba(0,0,0,0.6)
```

### 12.5 Animation

- Library: Framer Motion for meaningful state transitions
- Timing: fast and purposeful — 150ms (micro), 250ms (standard), 400ms (page)
- Easing: ease-out for entrances, ease-in for exits
- AI activity indicator: soft pulsing teal dot (--accent-teal) with
  CSS animation: pulse 1.5s ease-in-out infinite. Idle: static dim dot.
- No decorative or looping animations that distract during work

### 12.6 Responsive Behavior

- Minimum supported viewport: 1280px (professional tool, not mobile-first)
- Sidebar collapses to icon-only below 1440px
- Editor layout is a 3-column CSS grid:
    AssetBrowser (240px fixed) | VideoPlayer + Timeline (flex grow) | ChatPanel (320px fixed)
- Future mobile / desktop (Electron) share the same backend API

---

## 13. Frontend — Page and Component Spec

### Dashboard Page (/dashboard)

- Grid of ProjectCards: thumbnail, name, target platform badge, last edited, status
- "New Project" button → modal: name + platform + quick goal input
- Filtering by platform and status; sorting by date modified
- Empty state: illustrated prompt to create first project, clear CTA

### Editor Page (/project/[id])

Three-column layout, full viewport height, no scroll on the outer container:

```
┌────────────────┬──────────────────────────────┬──────────────┐
│  AssetBrowser  │        VideoPlayer            │  ChatPanel   │
│                │                               │              │
│  uploaded      │   preview (9:16 or 16:9)      │  correction  │
│  material grid │                               │  chat UI     │
│  with metadata │ ─────────────────────────     │              │
│  quality badge │        Timeline               │  AgentLog    │
│  hover-to-play │   segments + keyframes        │  (collapsed) │
│                │                               │              │
│                │   AgentLog (collapsible bar)  │  ModelSel.   │
└────────────────┴──────────────────────────────┴──────────────┘
```

**VideoPlayer**
- Custom dark skin, no browser-default controls
- Frame-accurate scrubbing via click-and-drag on progress bar
- Aspect ratio toggle: 9:16 / 1:1 / 16:9 (applies letterbox/pillarbox)
- Playback speed selector: 0.5x, 1x, 1.5x, 2x
- Before/after toggle: compare current draft with previous version

**Timeline**
- Horizontal scrollable strip beneath the video player
- Each segment rendered as a colored block with:
    - Thumbnail (proxy frame from midpoint of segment)
    - Duration label
    - Asset name label
    - Speed indicator if speed != 1.0
    - Text overlay indicator dot if overlay exists
- Drag-to-reorder segments (emits correction intent automatically)
- Click segment → segment metadata popover (source clip, in/out times, quality score)
- Playhead synced bidirectionally with VideoPlayer

**AssetBrowser**
- Grid of asset cards: 240px panel, 2-column grid
- Each card: thumbnail, filename, duration, quality score badge (color-coded)
- Hover: play preview in-place (muted autoplay of proxy)
- Drag asset onto Timeline to manually insert at position
- Filter by quality score, tag, or free-text search

**ChatPanel**
- Full conversation history, newest at bottom
- User messages: right-aligned, --accent background, DM Sans
- Agent responses: left-aligned, --bg-elevated background
  Each agent response shows: which agent responded, which model was used,
  confidence or ambiguity note if applicable
- Typing indicator (three dots animation) when agent is processing
- Input: multiline textarea, send on Ctrl+Enter or Send button
- Pinned quick-action chips above input:
    "Re-plan", "Add subtitles", "Add voiceover", "Export"

**AgentLog**
- Collapsible panel anchored to the bottom of the center column
- Collapsed: 32px strip showing current node name + pulsing indicator
- Expanded: scrollable list of TraceEvent entries, newest at top
- Each entry: node badge, agent name, event type, duration, model+tokens
- Expandable row: input/output summary, FFmpeg command if applicable
- Color coded by node for quick visual scanning

**ModelSelector**
- Small dropdown in the top-right of the header
- Shows: provider logo (small icon) + model name + latency estimate
- Per-task override: separate selector for understanding vs planning vs correction
- Shows health status dot (green / yellow / red) per provider

### Settings Page (/settings)

Sections:
- API Keys: per-provider masked input with "Test Connection" button + status
- Default Models: per-task dropdown from dynamically fetched available model list
- Ollama: base URL input, list of pulled models, "Pull Model" input
- Storage: backend toggle (local / S3), credential fields
- Preferences: language, default platform, default export quality

---

## 14. Video Processing Pipeline

### 14.1 Ingest and Probe

On upload:
- Run ffprobe immediately → extract duration, resolution, fps, codec, bitrate,
  audio presence, audio codec
- Reject if: file exceeds MAX_UPLOAD_SIZE_MB, or codec is not supported
  (supported: H.264, H.265, VP9, ProRes; audio: AAC, MP3, PCM)
- Generate poster thumbnail (first non-black frame via FFmpeg)
- Store all probe data in VideoAsset record

### 14.2 Keyframe Extraction

For each asset before understanding:
- Extract one frame every 2 seconds (configurable), maximum 30 frames per asset
- Save as JPEG quality 85 to /storage/keyframes/{asset_id}/frame_XXXX.jpg
- Generate 240p proxy video for Timeline thumbnails (fast encode, no audio)
- Store frame count and paths for use by Understand Agent

### 14.3 FFmpeg Command Suite

All commands are built as typed Python objects, serialized to command strings,
executed via a sandboxed subprocess runner with:
- Isolated working directory per job
- stdout and stderr captured and stored in TraceEvent
- Hard timeout enforced per command
- Non-zero exit code raises FFmpegError with full stderr attached

Core command types:

| Command          | FFmpeg approach                                      |
|------------------|------------------------------------------------------|
| probe            | ffprobe -v quiet -print_format json -show_streams    |
| trim             | -ss {start} -to {end} -c copy (stream copy, fast)    |
| resize           | scale + pad filter to target aspect ratio            |
| speed            | setpts + atempo filters                              |
| concat           | concat demuxer (cut transitions, no re-encode)       |
| fade             | xfade filter (fade, dissolve, slide transitions)     |
| text_overlay     | drawtext filter with fontfile, fontsize, color, box  |
| burn_subtitle    | subtitles filter with ASS file path                  |
| audio_mix        | amix + volume filters for BGM + voiceover + original |
| audio_normalize  | loudnorm filter for consistent perceived loudness    |
| final_render     | Full encode: libx264 / aac, target bitrate for platform|

### 14.4 Full Render Pipeline Execution Order

1. Per segment: trim → resize → speed adjustment → text_overlay → save temp_{segment_id}.mp4
2. Concat all temp segment files via concat demuxer → draft_concat.mp4
3. If bgm_requested: amix BGM at configured volume with fade-out → draft_bgm.mp4
4. If voiceover: mix TTS audio, duck original audio -20dB during voiceover → draft_vo.mp4
5. Normalize audio loudness → draft_normalized.mp4
6. If subtitle_requested: burn ASS subtitle file → draft_sub.mp4
7. Final encode to platform bitrate and codec → draft_{version}.mp4

### 14.5 Platform Presets

| Platform     | Aspect Ratio | Recommended Bitrate | Max Duration |
|--------------|--------------|---------------------|--------------|
| Douyin       | 9:16         | 4 Mbps              | 60s / 15min  |
| Xiaohongshu  | 9:16 or 3:4  | 3 Mbps              | 15min        |
| Taobao/Tmall | 1:1 or 16:9  | 3 Mbps              | 60s          |
| Bilibili     | 16:9         | 6 Mbps              | unlimited    |
| Custom       | user-defined | user-defined        | user-defined |

---

## 15. Natural Language Correction

### 15.1 Supported Operation Types

| Example User Input                           | Operation Type        | Re-run Scope               |
|----------------------------------------------|-----------------------|----------------------------|
| 把第2段换成室外那个镜头                            | swap_clip             | execute → subtitle → tts   |
| 开头3秒加快到1.5倍                               | set_speed             | execute → subtitle → tts   |
| 去掉第3段                                       | remove_segment        | execute → subtitle → tts   |
| 在第1段结尾加个淡入效果                             | update_transition     | execute                     |
| 字幕字体改大，颜色改红色                             | update_subtitle_style | subtitle                   |
| 把字幕全部删掉                                    | remove_subtitles      | subtitle                   |
| 配音语气太正式，换轻松点的                            | update_tts_style      | tts                        |
| 配音换成女声                                     | update_tts_voice      | tts                        |
| 去掉配音，只保留原声                                | remove_tts            | tts                        |
| 整体压缩到20秒                                   | update_duration       | plan → execute → subtitle → tts |
| 帮我重新规划剪辑顺序，按卖点排列                        | replan                | plan → execute → subtitle → tts |
| 背景音乐音量调小一点                                | update_bgm_volume     | execute                    |
| 第一段的文字改成"限时8折"                            | update_text_overlay   | execute                    |
| 在第2段和第3段之间加一个产品特写                        | insert_segment        | execute → subtitle → tts   |

### 15.2 Intent Parsing Process

The Correct Agent sends the user's raw message to the text LLM with:
- Current EditScript (full, serialized as JSON)
- List of all available assets with their IDs and scene descriptions
- Correction operation taxonomy (the table above)
- Strict instruction to return only a valid CorrectionIntent JSON object

Self-correction loop applies: if output fails Pydantic validation, retry with
error message appended (max 3 times). Then fallback model if still failing.

### 15.3 Ambiguity Handling

If the parsed intent has an ambiguous target (e.g. "那个室外镜头" matches multiple
assets), the Correct Agent:
- Returns an AmbiguityResponse instead of CorrectionIntent
- Lists the candidate assets with thumbnails and descriptions
- human_review node surfaces the options in ChatPanel as clickable choices
- User selects the intended asset; graph resumes with unambiguous CorrectionIntent

---

## 16. Error Handling and Resilience

### 16.1 Error Taxonomy

| Error Class            | Examples                                  | Handling Strategy                                    |
|------------------------|-------------------------------------------|------------------------------------------------------|
| ModelAPIError          | rate limit, network timeout               | Retry with backoff → route to fallback model         |
| ModelOutputError       | schema fail, incoherent output            | Self-correction loop (max 3) → fallback model        |
| FFmpegError            | non-zero exit, corrupt segment output     | Retry once → skip segment + notify user              |
| AssetError             | file not found, corrupt video             | Fail immediately, surface clear error to user        |
| StorageError           | disk full, OSS error                      | Retry → alert user                                   |
| NodeTimeoutError       | node exceeded hard timeout                | Supervisor: retry or degrade gracefully              |
| MaxIterationsExceeded  | agent looped N times, no valid output     | Fail node, surface last output for user review       |
| CircuitOpenError       | provider circuit breaker open             | Route to fallback provider immediately               |
| AmbiguityError         | correction intent is ambiguous            | Surface choices to user via human_review node        |

### 16.2 Graceful Degradation

- Subtitle node fails: output video without subtitles, notify user, offer manual retry
- TTS node fails: output video without voiceover, notify user, offer manual retry
- Single segment fails to render: skip that segment, continue with remaining,
  notify user which segment was skipped and why
- All fallback models exhausted: surface error to user with the last raw model
  output and a "try again" option

### 16.3 Job State Persistence

Full AgentState checkpointed after each node via LangGraph PostgreSQL checkpointer.
If the server restarts or a Celery worker dies mid-job:
- Celery retries the task (max_retries=3, countdown=10s)
- LangGraph resumes from the last successful checkpoint
- No completed node work is repeated
- In-progress node re-runs from its beginning (idempotent node design required)

Idempotency requirement: every node must be safe to re-run from scratch.
FFmpeg output files are written to job-scoped temp directories and deterministically named.

---

## 17. Storage and File Management

### 17.1 Directory Layout

```
storage/
├── assets/
│   └── {project_id}/
│       └── {asset_id}.{ext}           # original uploaded file
├── keyframes/
│   └── {asset_id}/
│       └── frame_0001.jpg             # extracted keyframes (JPEG 85)
├── proxies/
│   └── {asset_id}_240p.mp4            # low-res proxy for timeline thumbnails
├── temp/
│   └── {job_id}/
│       ├── seg_{segment_id}.mp4       # per-segment render output
│       ├── draft_concat.mp4
│       ├── draft_bgm.mp4
│       └── draft_{version}.mp4        # versioned draft for preview
├── outputs/
│   └── {project_id}/
│       ├── draft_v1.mp4
│       ├── draft_v2.mp4               # keep last 3 versions
│       └── final.mp4                  # confirmed export
└── tts/
    └── {job_id}/
        └── voiceover.mp3              # TTS-generated audio
```

### 17.2 Storage Abstraction

StorageBackend interface with two implementations:
- LocalStorageBackend: reads and writes to STORAGE_PATH on local filesystem
- S3StorageBackend: reads and writes to S3-compatible OSS;
  generates presigned URLs for direct browser upload and download

All file references in the database are stored as logical keys
(e.g. assets/{project_id}/{asset_id}.mp4), resolved to actual access URLs at
request time by the storage abstraction layer.

### 17.3 Cleanup Policy

- temp/ directory for a job is deleted after successful export
- Draft outputs beyond the last 3 versions are deleted automatically
- Asset deletion cascades: removes asset file, keyframes, proxies, all DB records
- Orphaned temp directories (jobs in failed state > 24h) cleaned by scheduled task

---

## 18. Infrastructure and Deployment

### 18.1 docker-compose.yml (Local Dev)

Services:
- api: FastAPI (uvicorn with hot reload, port 8000)
- worker: Celery worker (concurrency 1 for dev, all queues)
- frontend: Next.js dev server (port 3000)
- postgres: PostgreSQL 16 (port 5432)
- redis: Redis 7 (port 6379)
- minio: MinIO S3-compatible storage (API port 9000, console port 9001)
- jaeger: Jaeger all-in-one (UI port 16686, OTLP port 4317)
- prometheus: Prometheus scraping api and worker (port 9090)
- grafana: Grafana with pre-built dashboard (port 3001)

### 18.2 Production Configuration

- All services in Docker with pinned image versions and resource limits
- Celery workers: one process per CPU core, separate queues for
  understanding (GPU-heavy), rendering (CPU-heavy), and general tasks
- Nginx: reverse proxy for API and frontend; client_max_body_size 2048m
  for large video uploads; gzip for API responses
- PostgreSQL with PgBouncer for connection pooling
- Redis with appendonly yes for persistence
- FFmpeg installed on worker nodes, not on API nodes
- Whisper model pre-downloaded to worker nodes at Docker build time
- Object storage: Aliyun OSS or any S3-compatible service

### 18.3 Health Checks

```
GET /health                 API status, DB connectivity, Redis connectivity
GET /health/models          Per-provider model API health check
GET /health/storage         Storage backend write test
GET /metrics                Prometheus metrics endpoint
```

---

## 19. Environment Variables

```bash
# ── Application ──────────────────────────────────────────────────
APP_ENV=development                       # development | production
SECRET_KEY=change-me-in-production
CORS_ORIGINS=http://localhost:3000

# ── Database ─────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://mixcut:mixcut@localhost:5432/mixcut
REDIS_URL=redis://localhost:6379/0

# ── Storage ──────────────────────────────────────────────────────
STORAGE_BACKEND=local                     # local | s3
STORAGE_PATH=./storage
S3_ENDPOINT=
S3_BUCKET=mixcut
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_REGION=
MAX_UPLOAD_SIZE_MB=2048

# ── Model Providers ──────────────────────────────────────────────
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
DASHSCOPE_API_KEY=
DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_AUTO_PULL=true

# ── Default Model Selection ───────────────────────────────────────
MODEL_VIDEO_UNDERSTANDING=qwen3-vl
MODEL_EDIT_PLANNING=claude-sonnet-4
MODEL_CORRECTION_INTENT=claude-sonnet-4
MODEL_TTS_SCRIPT=qwen3

# ── FFmpeg ───────────────────────────────────────────────────────
FFMPEG_BIN=ffmpeg
FFPROBE_BIN=ffprobe
FFMPEG_TIMEOUT_SECONDS=300
FFMPEG_THREADS=4

# ── Whisper ──────────────────────────────────────────────────────
WHISPER_MODEL=large-v3
WHISPER_LANGUAGE=zh
WHISPER_DEVICE=cpu                        # cpu | cuda | mps

# ── TTS ──────────────────────────────────────────────────────────
MINIMAX_API_KEY=
MINIMAX_GROUP_ID=
VOLCENGINE_TTS_APP_ID=
VOLCENGINE_TTS_ACCESS_TOKEN=

# ── Agent Harness ────────────────────────────────────────────────
AGENT_MAX_ITERATIONS=10
AGENT_NODE_TIMEOUT_UNDERSTAND=120
AGENT_NODE_TIMEOUT_PLAN=60
AGENT_NODE_TIMEOUT_EXECUTE=300
AGENT_NODE_TIMEOUT_SUBTITLE=180
AGENT_NODE_TIMEOUT_TTS=120
AGENT_NODE_TIMEOUT_CORRECT=30
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# ── Observability ─────────────────────────────────────────────────
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
PROMETHEUS_METRICS_ENABLED=true
LOG_LEVEL=INFO
```

---

## 20. Development Priorities

Implement strictly in phase order. Each phase must be working end-to-end
before the next phase begins. Do not skip ahead.

### Phase 1 — Foundation
1. docker-compose.yml with all services (postgres, redis, minio, jaeger, prometheus, grafana)
2. SQLAlchemy ORM models (Project, VideoAsset, RenderJob, EditScript, CorrectionHistory)
3. Alembic initial migration
4. FastAPI app skeleton: all routers mounted, all endpoints return 501 Not Implemented
5. Pydantic v2 schemas for all request/response types
6. structlog configuration (JSON output, consistent fields)
7. GET /health endpoint
8. Config module (Pydantic Settings, all env vars)

### Phase 2 — File Pipeline
9. POST /projects/{id}/assets upload endpoint
   (multipart, size validation, mime type check)
10. ffprobe integration on upload → populate VideoAsset fields
11. Poster thumbnail generation (FFmpeg, first non-black frame)
12. Keyframe extraction utility (FFmpeg, configurable interval)
13. 240p proxy generation (FFmpeg, fast encode)
14. GET /projects/{id}/assets endpoint with full metadata
15. Storage abstraction layer (LocalStorageBackend implemented and tested)

### Phase 3 — Model Layer
16. ModelProvider abstract base class
17. Anthropic provider
18. OpenAI provider
19. DashScope provider (Qwen3-VL + Qwen3 text)
20. Ollama provider (generic, auto-pull support)
21. Google Gemini provider
22. Model registry with default task routing
23. GET /models endpoint with health status per provider

### Phase 4 — Agent Core
24. AgentState TypedDict
25. LangGraph graph skeleton: all nodes defined as stubs, edges wired correctly
26. PostgreSQL checkpointer setup and integration test
27. Celery task: launch graph, persist state after each node, publish SSE events
28. Redis pub/sub → SSE progress stream (GET /jobs/{id}/stream)
29. GET /jobs/{id} endpoint (status + trace)
30. POST /projects/{id}/jobs to start a job

### Phase 5 — Harness Layer
31. Retry decorator (exponential backoff + jitter, per-error-type policy)
32. Timeout enforcement wrapper (asyncio.wait_for per node)
33. Circuit breaker (per provider, configurable thresholds)
34. Output schema validation between nodes (Pydantic strict mode + semantic checks)
35. Self-correction loop (max 3, error message appended to prompt)
36. MaxIterationsExceeded handling
37. Graceful degradation (subtitle/TTS failure → continue without, notify user)

### Phase 6 — Specialist Agents and Nodes
38. Understand Agent: keyframe → Qwen3-VL → ClipMetadata parsing
    - Fan-out per asset using LangGraph Send API
    - Fan-in merge all ClipMetadata into state
    - Cache: skip assets with existing metadata in state.node_outputs
39. Plan Agent: ClipMetadata + UserGoal → Claude → EditScript parsing
    - Include planning_rationale in output
    - Semantic validation: total duration within ±10% of target
40. Execute Agent: EditScript → FFmpeg pipeline → draft video
    - All FFmpeg command types implemented and tested
    - Per-segment error isolation
41. Subtitle Agent: Whisper → LLM polish → ASS file → burn-in
42. TTS Agent: LLM script → MiniMax TTS → audio mix → output video
43. human_review node: suspend graph, publish SSE event, wait for API resume signal
44. POST /jobs/{id}/resume endpoint

### Phase 7 — Correction Loop
45. Correct Agent: intent parsing → CorrectionIntent → affected_nodes determination
46. Ambiguity handling: AmbiguityResponse → surface choices in human_review
47. Partial re-run routing in supervisor_route (skip cached nodes)
48. POST /projects/{id}/correct endpoint
49. Correction history persistence and GET endpoint

### Phase 8 — Frontend Core
50. Next.js 15 project setup (App Router, TypeScript strict, Tailwind 4)
51. CSS variables and design tokens (globals.css, tokens.css)
52. Typography setup (DM Sans + JetBrains Mono import)
53. UI primitives: Button, Input, Badge, Card, Modal, Progress, Tooltip, Toast
54. Sidebar, Header, StatusBar layout components with AI activity indicator
55. Dashboard page: ProjectCard grid, NewProjectModal
56. Upload flow page: drag-and-drop, multipart upload with progress bar, asset grid

### Phase 9 — Editor UI
57. VideoPlayer component (custom skin, scrubbing, aspect ratio toggle, before/after)
58. Timeline component (segment blocks, thumbnails, drag-to-reorder, playhead sync)
59. AssetBrowser component (grid, hover-to-play, quality badge, drag-to-timeline)
60. ChatPanel component (conversation history, agent attribution, quick action chips)
61. AgentLog component (live SSE trace, collapsible, per-node color coding)
62. ModelSelector component (per-task override, health status dots)
63. SSE hook (lib/sse.ts) for live job progress
64. TanStack Query hooks for all API resources

### Phase 10 — Export and Settings
65. ExportPanel component: format, quality, platform preset selector
66. POST /projects/{id}/export endpoint
67. GET /projects/{id}/download endpoint
68. Settings page: API keys, model defaults, Ollama config, storage, preferences

### Phase 11 — Observability
69. OpenTelemetry tracer: spans for all nodes, model calls, FFmpeg commands
70. Prometheus metrics: all metrics in section 11.3 implemented
71. Grafana dashboard JSON (import-ready, covers all key metrics)
72. Jaeger integration verified end-to-end on a full job run

### Phase 12 — Hardening and Polish
73. Rate limiting on upload and job creation endpoints
74. Input sanitization (filenames, user text, all external inputs)
75. Full error handling audit (every error class handled per taxonomy in section 16)
76. S3StorageBackend implementation and integration test
77. docker-compose.prod.yml + nginx.conf
78. .env.example with all variables documented
79. End-to-end smoke test: upload 3 clips → run job → preview → correct → export
80. README: setup instructions, architecture diagram, quickstart

---

## 21. Code Standards

### Python

- Formatter: Black, line-length=100
- Linter: Ruff with all rules enabled, auto-fix on save
- Type hints: mandatory on all function signatures and class attributes
- Async: async/await throughout; no blocking calls in async context;
  use asyncio.to_thread() for CPU-bound operations
- Pydantic v2: model_config = ConfigDict(strict=True) on all schemas
- SQLAlchemy: 2.0 style only (select(), async sessions); no legacy Query API
- Exception classes: custom exception for every error category in section 16;
  never catch bare Exception silently; always log with full context
- Logging: structlog.get_logger() with bound context fields;
  never use print() anywhere in the codebase
- Prompt strings: all LLM prompts defined in agent/prompts/ as versioned
  template strings; never inline in node or agent code
- No hardcoded values: all configuration via config.py from environment variables
- No commented-out code: delete instead of comment out

### TypeScript / Frontend

- Strict mode: "strict": true in tsconfig.json
- No any: zero tolerance; use unknown and narrow with type guards
- API calls: all via typed client in lib/api.ts; never raw fetch in components
- Server state: TanStack Query for all API data; no useEffect for data fetching
- Client state: Zustand for global UI state; no prop drilling beyond 2 levels
- Components: functional only; no class components; no default export for
  components (use named exports)
- Styling: Tailwind utility classes only; no inline style prop; no CSS modules;
  design token values only via CSS variables, never hardcoded
- File naming: PascalCase for components, camelCase for utilities and hooks,
  kebab-case for route segments

### General

- All Docker images: pinned to specific digest or version tag, never :latest
- All Alembic migrations: every schema change has a migration;
  never run Base.metadata.create_all() in any environment
- All FFmpeg commands: logged at DEBUG level with full command string before execution
- All model calls: logged at DEBUG level with prompt summary and response summary
- All temp files: written to job-scoped directory; cleaned up on job completion
- Idempotency: every LangGraph node must be safe to re-run from scratch
- Tests: each agent node has a unit test with mocked model and mocked FFmpeg;
  each API endpoint has an integration test against a test database
