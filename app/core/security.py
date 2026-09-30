import time
from collections import defaultdict

from fastapi import Header, HTTPException, Request, status

from app.core.config import get_settings

settings = get_settings()

# In-memory sliding window rate limiter
_request_records: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(request: Request) -> None:
    """
    Sliding window rate limiter based on client IP.
    Allows up to RATE_LIMIT_PER_MINUTE requests per 60 seconds.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    window = 60.0

    # Prune timestamps older than 60s
    timestamps = [t for t in _request_records[client_ip] if (now - t) < window]
    _request_records[client_ip] = timestamps

    if len(timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute allowed.",
            headers={"Retry-After": "60"},
        )

    _request_records[client_ip].append(now)


def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
) -> bool:
    """
    Validate API key when API_KEY_ENABLED is True.
    Supports either 'X-API-Key: <key>' or 'Authorization: Bearer <key>'.
    """
    if not settings.API_KEY_ENABLED:
        return True

    configured_key = settings.API_KEY
    if not configured_key:
        return True

    from fastapi.params import Header as HeaderParam
    clean_api_key = x_api_key if not isinstance(x_api_key, HeaderParam) else None
    clean_auth = authorization if not isinstance(authorization, HeaderParam) else None

    provided_key = clean_api_key
    if not provided_key and clean_auth and clean_auth.startswith("Bearer "):
        provided_key = clean_auth[7:].strip()

    if provided_key != configured_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return True
