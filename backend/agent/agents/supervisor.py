from __future__ import annotations

from backend.observability.logging import get_logger
from backend.schemas.correction import CorrectionScope

logger = get_logger(__name__)


def determine_rerun_nodes(affected_nodes: list[CorrectionScope]) -> list[str]:
    node_map = {
        CorrectionScope.UNDERSTAND: ["understand"],
        CorrectionScope.PLAN: ["plan"],
        CorrectionScope.EXECUTE: ["execute"],
        CorrectionScope.SUBTITLE: ["subtitle"],
        CorrectionScope.TTS: ["tts"],
    }
    downstream: dict[str, list[str]] = {
        "understand": ["plan", "execute"],
        "plan": ["execute"],
        "execute": ["subtitle", "tts"],
        "subtitle": [],
        "tts": [],
    }
    rerun: set[str] = set()
    for scope in affected_nodes:
        for node in node_map.get(scope, []):
            rerun.add(node)
            for _ in range(3):
                for parent, children in downstream.items():
                    if parent in rerun:
                        rerun.update(children)
    return list(rerun) or ["plan", "execute"]