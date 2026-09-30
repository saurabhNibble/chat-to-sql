from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.core.security import check_rate_limit, verify_api_key


def test_rate_limiter_allows_normal_traffic():
    request = MagicMock()
    request.client.host = "192.168.1.100"
    # Should not raise
    check_rate_limit(request)


def test_rate_limiter_blocks_burst_traffic():
    request = MagicMock()
    request.client.host = "192.168.1.200"

    settings = get_settings()
    orig_limit = settings.RATE_LIMIT_PER_MINUTE
    settings.RATE_LIMIT_PER_MINUTE = 3
    try:
        check_rate_limit(request)
        check_rate_limit(request)
        check_rate_limit(request)
        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(request)
        assert exc_info.value.status_code == 429
    finally:
        settings.RATE_LIMIT_PER_MINUTE = orig_limit


def test_verify_api_key_when_disabled():
    settings = get_settings()
    settings.API_KEY_ENABLED = False
    assert verify_api_key(x_api_key=None, authorization=None) is True


def test_verify_api_key_when_enabled():
    settings = get_settings()
    settings.API_KEY_ENABLED = True
    settings.API_KEY = "secret-key-123"
    try:
        # Correct header
        assert verify_api_key(x_api_key="secret-key-123") is True
        # Correct Bearer token
        assert verify_api_key(authorization="Bearer secret-key-123") is True
        # Wrong key
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(x_api_key="wrong-key")
        assert exc_info.value.status_code == 401
    finally:
        settings.API_KEY_ENABLED = False
        settings.API_KEY = None
