from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Learner full name")
    email: str = Field(..., min_length=3, max_length=255, description="Learner email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password")


class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, description="Learner email address")
    password: str = Field(..., description="Password")


class OAuthLoginRequest(BaseModel):
    provider: str = Field(..., description="OAuth provider: 'google' or 'github'")
    email: str | None = Field(default=None, description="Email if provided by OAuth callback/demo")
    name: str | None = Field(default=None, description="Name if provided by OAuth")
    avatar_url: str | None = Field(default=None, description="Avatar image URL")


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    avatar_url: str | None = None
    provider: str = "local"
    created_at: float


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
