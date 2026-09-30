from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_auth_service, get_current_user
from app.models.auth import (
    AuthResponse,
    OAuthLoginRequest,
    UserLoginRequest,
    UserProfile,
    UserRegisterRequest,
)
from app.services.auth import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new learner account",
)
def register(
    request: UserRegisterRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        user, token = auth_svc.register(request.name, request.email, request.password)
        return AuthResponse(access_token=token, user=user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in with email and password",
)
def login(
    request: UserLoginRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        user, token = auth_svc.login(request.email, request.password)
        return AuthResponse(access_token=token, user=user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post(
    "/oauth/google",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Continue with Google / Gmail",
)
def oauth_google(
    request: OAuthLoginRequest | None = None,
    auth_svc: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    email = (request.email if request and request.email else "learner@gmail.com")
    name = (request.name if request and request.name else "Google Learner")
    avatar = (
        request.avatar_url
        if request and request.avatar_url
        else f"https://api.dicebear.com/7.x/bottts/svg?seed={email}"
    )
    user, token = auth_svc.oauth_login(
        provider="google",
        email=email,
        name=name,
        avatar_url=avatar,
    )
    return AuthResponse(access_token=token, user=user)


@router.post(
    "/oauth/github",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Continue with GitHub",
)
def oauth_github(
    request: OAuthLoginRequest | None = None,
    auth_svc: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    email = (request.email if request and request.email else "developer@github.com")
    name = (request.name if request and request.name else "GitHub Developer")
    avatar = (
        request.avatar_url
        if request and request.avatar_url
        else f"https://api.dicebear.com/7.x/identicon/svg?seed={email}"
    )
    user, token = auth_svc.oauth_login(
        provider="github",
        email=email,
        name=name,
        avatar_url=avatar,
    )
    return AuthResponse(access_token=token, user=user)


@router.get(
    "/me",
    response_model=UserProfile,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
def get_me(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    return current_user
