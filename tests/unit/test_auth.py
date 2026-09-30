import uuid

import pytest

from app.services.auth import AuthService


def test_auth_register_and_login():
    auth_svc = AuthService()
    email = f"learner_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecretPassword123!"
    name = "Test Learner"

    # Register
    user, token = auth_svc.register(name, email, password)
    assert user.email == email
    assert user.name == name
    assert token is not None

    # Login
    logged_user, login_token = auth_svc.login(email, password)
    assert logged_user.id == user.id
    assert login_token is not None

    # Duplicate registration fails
    with pytest.raises(ValueError, match="already exists"):
        auth_svc.register(name, email, password)


def test_auth_oauth_google_and_github():
    auth_svc = AuthService()

    user_g, token_g = auth_svc.oauth_login("google", "test_google@gmail.com", "Google User")
    assert user_g.provider == "google"
    assert token_g is not None

    user_gh, token_gh = auth_svc.oauth_login("github", "test_gh@github.com", "GitHub User")
    assert user_gh.provider == "github"
    assert token_gh is not None


def test_auth_invalid_credentials():
    auth_svc = AuthService()
    with pytest.raises(ValueError, match="Invalid email or password"):
        auth_svc.login("non_existent@example.com", "bad_pass")
