from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WhisperConfig:
    model: str = "large-v3"
    language: str = "zh"
    device: str = "cpu"


@dataclass
class TranscriptionResult:
    text: str
    segments: list[dict]
    language: str


async def transcribe_audio(
    audio_path: str | Path,
    config: WhisperConfig | None = None,
) -> TranscriptionResult:
    config = config or WhisperConfig()
    audio_path = Path(audio_path)
    try:
        import whisper
    except ImportError:
        logger.warning("whisper_not_installed", extra={"path": str(audio_path)})
        return TranscriptionResult(text="", segments=[], language=config.language)
    model = whisper.load_model(config.model, device=config.device)
    result = await asyncio.to_thread(
        model.transcribe,
        str(audio_path),
        language=config.language,
    )
    return TranscriptionResult(
        text=result["text"].strip(),
        segments=result.get("segments", []),
        language=result.get("language", config.language),
    )