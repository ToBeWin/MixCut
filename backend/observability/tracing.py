from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from backend.config import Settings

_tracer = None


def configure_tracing(settings: Settings) -> None:
    global _tracer
    endpoint = getattr(settings, "otel_exporter_otlp_endpoint", None)
    if not endpoint:
        _tracer = None
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("mixcut")
    except ImportError:
        _tracer = None


@contextmanager
def span(name: str, attributes: dict | None = None) -> Iterator[None]:
    if _tracer is None:
        yield
        return
    with _tracer.start_as_current_span(name, attributes=attributes):
        yield