"""Tests for input sanitization utilities."""

from __future__ import annotations

import pytest

from backend.sanitize import sanitize_filename, sanitize_user_text


class TestSanitizeFilename:
    def test_normal_filename(self):
        assert sanitize_filename("video.mp4") == "video.mp4"

    def test_strips_path_traversal(self):
        assert sanitize_filename("../../etc/passwd") == "passwd"
        assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"

    def test_strips_special_chars(self):
        result = sanitize_filename("file<script>alert(1)</script>.mp4")
        assert "<" not in result
        assert ">" not in result
        assert "script" in result

    def test_strips_null_bytes(self):
        result = sanitize_filename("file\x00.mp4")
        assert "\x00" not in result

    def test_collapses_whitespace(self):
        result = sanitize_filename("my   file   name.mp4")
        assert "  " not in result

    def test_preserves_extension(self):
        result = sanitize_filename("a" * 300 + ".mp4")
        assert result.endswith(".mp4")
        assert len(result) <= 200

    def test_empty_returns_unnamed(self):
        assert sanitize_filename("") == "unnamed"

    def test_dots_only_returns_dots(self):
        # "..." has chars after stripping, so it's preserved
        result = sanitize_filename("...")
        assert result == "..."

    def test_unicode_normalization(self):
        result = sanitize_filename("Á.mp4")  # A + combining accent
        assert result == "Á.mp4"  # normalized to precomposed


class TestSanitizeUserText:
    def test_normal_text(self):
        assert sanitize_user_text("Hello world") == "Hello world"

    def test_strips_control_chars(self):
        result = sanitize_user_text("Hello\x00\x01\x02world")
        assert result == "Helloworld"

    def test_preserves_newlines_and_tabs(self):
        result = sanitize_user_text("line1\nline2\ttab")
        assert "\n" in result
        assert "\t" in result

    def test_strips_leading_trailing_whitespace(self):
        assert sanitize_user_text("  hello  ") == "hello"

    def test_truncates_long_text(self):
        long_text = "a" * 6000
        result = sanitize_user_text(long_text, max_len=5000)
        assert len(result) == 5000

    def test_custom_max_len(self):
        result = sanitize_user_text("hello", max_len=3)
        assert result == "hel"

    def test_empty_text(self):
        assert sanitize_user_text("") == ""
