from __future__ import annotations

from fastapi import APIRouter, Response

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

    jobs_total = Counter("mixcut_jobs_total", "Total jobs", ["status"])
    job_duration_seconds = Histogram("mixcut_job_duration_seconds", "Job duration")
    node_duration_seconds = Histogram("mixcut_node_duration_seconds", "Node duration", ["node", "agent"])
    model_call_duration_seconds = Histogram(
        "mixcut_model_call_duration_seconds", "Model call duration", ["provider", "model"]
    )
    model_tokens_total = Counter("mixcut_model_tokens_total", "Model tokens", ["provider", "model", "type"])
    ffmpeg_command_duration_seconds = Histogram(
        "mixcut_ffmpeg_command_duration_seconds", "FFmpeg command duration", ["command_type"]
    )
    ffmpeg_errors_total = Counter("mixcut_ffmpeg_errors_total", "FFmpeg errors", ["command_type"])
    corrections_total = Counter("mixcut_corrections_total", "Corrections", ["operation_type"])
    active_jobs = Gauge("mixcut_active_jobs", "Active jobs")
    circuit_breaker_state = Gauge("mixcut_circuit_breaker_state", "Circuit breaker state", ["provider"])

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

metrics_router = APIRouter()


@metrics_router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    if PROMETHEUS_AVAILABLE:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    return Response("# MixCut metrics - prometheus_client not installed\n", media_type="text/plain")