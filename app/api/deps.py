from functools import lru_cache

from fastapi import Header, HTTPException, status

from app.models.auth import UserProfile
from app.services.auth import auth_service
from app.services.conversation import conversation_store
from app.services.query_service import QueryService


@lru_cache
def get_query_service() -> QueryService:
    return QueryService()


def get_conversation_store():
    return conversation_store


def get_auth_service():
    return auth_service


def get_optional_user(authorization: str | None = Header(default=None)) -> UserProfile | None:
    if not authorization:
        return None
    try:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None
        payload = auth_service.decode_access_token(token)
        if not payload or not payload.get("sub"):
            return None
        return auth_service.get_user_by_id(payload["sub"])
    except Exception:
        return None


def get_current_user(authorization: str | None = Header(default=None)) -> UserProfile:
    user = get_optional_user(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or are invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
