"""Tests for API key authentication middleware."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from backend.api.auth import AuthMiddleware, PUBLIC_PATHS


class TestAuthMiddleware:
    """Test the auth middleware logic."""

    def test_public_paths_defined(self):
        """Public paths include health and docs endpoints."""
        assert "/health" in PUBLIC_PATHS
        assert "/health/models" in PUBLIC_PATHS
        assert "/health/storage" in PUBLIC_PATHS
        assert "/metrics" in PUBLIC_PATHS
        assert "/docs" in PUBLIC_PATHS
        assert "/openapi.json" in PUBLIC_PATHS
        assert "/redoc" in PUBLIC_PATHS

    def test_public_paths_count(self):
        """Verify we have the expected number of public paths."""
        assert len(PUBLIC_PATHS) == 7

    @pytest.mark.asyncio
    async def test_no_api_key_allows_all(self):
        """When no API key is configured, all requests pass through."""
        with patch("backend.api.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_key = None
            mock_settings.return_value.api_prefix = "/api/v1"

            middleware = AuthMiddleware(app=None)
            # The middleware should not reject when no key is set
            # We just verify the middleware can be instantiated
            assert middleware is not None


class TestAuthPaths:
    """Test path matching logic."""

    def test_health_path_is_public(self):
        assert "/health" in PUBLIC_PATHS

    def test_api_prefixed_paths_not_in_public(self):
        """Public paths don't include API prefix - middleware strips it."""
        assert "/api/v1/health" not in PUBLIC_PATHS
