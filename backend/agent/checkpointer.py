"""Checkpointer setup for LangGraph state persistence.

Provides PostgreSQL checkpointer for production and in-memory for development/testing.
"""

from __future__ import annotations

from pathlib import Path

from backend.schemas.agent_state import AgentState
from backend.observability.logging import get_logger

logger = get_logger(__name__)


class InMemoryCheckpointer:
    """Simple in-memory checkpointer for development and testing."""

    def __init__(self) -> None:
        self._states: dict[str, AgentState] = {}

    async def save(self, state: AgentState) -> None:
        self._states[state.job_id] = state

    async def load(self, job_id: str) -> AgentState | None:
        return self._states.get(job_id)

    async def delete(self, job_id: str) -> None:
        self._states.pop(job_id, None)


class FileCheckpointer:
    """File-based checkpointer for local development without PostgreSQL."""

    def __init__(self, storage_root: Path) -> None:
        self._root = storage_root / "checkpoints"
        self._root.mkdir(parents=True, exist_ok=True)

    async def save(self, state: AgentState) -> None:
        path = self._root / f"{state.job_id}.json"
        path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    async def load(self, job_id: str) -> AgentState | None:
        path = self._root / f"{job_id}.json"
        if not path.exists():
            return None
        data = path.read_text(encoding="utf-8")
        return AgentState.model_validate_json(data)

    async def delete(self, job_id: str) -> None:
        path = self._root / f"{job_id}.json"
        path.unlink(missing_ok=True)


def create_langgraph_checkpointer(database_url: str | None = None):
    """Create a LangGraph-compatible checkpointer.

    Uses PostgreSQL if database_url is provided and langgraph-checkpoint-postgres
    is available. Falls back to MemorySaver otherwise.

    Returns a checkpointer instance compatible with graph.compile(checkpointer=...).
    """
    if database_url:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            logger.info("checkpointer_postgres", url=_mask_url(database_url))
            return AsyncPostgresSaver.from_conn_string(database_url)
        except ImportError:
            logger.warning("checkpointer_postgres_unavailable", fallback="memory")
        except Exception as exc:
            logger.error("checkpointer_postgres_failed", error=str(exc), fallback="memory")

    from langgraph.checkpoint.memory import MemorySaver
    logger.info("checkpointer_memory")
    return MemorySaver()


def _mask_url(url: str) -> str:
    """Mask password in database URL for logging."""
    import re
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)
