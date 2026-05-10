"""Input sanitization utilities for user-provided data."""

from __future__ import annotations

import re
import unicodedata

# Characters unsafe in filenames across OS platforms
_UNSAFE_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
# Control characters (except newline/tab) in user text
_CONTROL_CHARS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def sanitize_filename(name: str, max_len: int = 200) -> str:
    """Sanitize a user-supplied filename.

    - Strips path traversal sequences
    - Removes OS-unsafe characters
    - Collapses whitespace
    - Limits length
    """
    # Strip path components
    name = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    # Remove unsafe characters
    name = _UNSAFE_FILENAME.sub("", name)
    # Normalize unicode
    name = unicodedata.normalize("NFC", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    # Limit length, preserving extension
    if len(name) > max_len:
        dot = name.rfind(".")
        if dot > 0:
            ext = name[dot:]
            name = name[: max_len - len(ext)] + ext
        else:
            name = name[:max_len]
    return name or "unnamed"


def sanitize_user_text(text: str, max_len: int = 5000) -> str:
    """Sanitize user-provided text input.

    - Strips control characters (except newline/tab)
    - Normalizes unicode
    - Limits length
    """
    text = _CONTROL_CHARS.sub("", text)
    text = unicodedata.normalize("NFC", text)
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len]
    return text
