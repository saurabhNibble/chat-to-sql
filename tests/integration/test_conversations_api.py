import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_auth_and_conversations_flow():
    # 1. Register learner
    learner_email = f"int_learner_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Integration Learner",
            "email": learner_email,
            "password": "Password123!",
        },
    )
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    token = data["access_token"]
    assert token

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get profile
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == learner_email

    # 3. Google OAuth
    google_resp = client.post(
        "/api/v1/auth/oauth/google",
        json={"provider": "google", "email": f"gmail_{uuid.uuid4().hex[:8]}@gmail.com", "name": "Gmail Learner"},
    )
    assert google_resp.status_code == 200
    assert google_resp.json()["user"]["provider"] == "google"

    # 4. GitHub OAuth
    github_resp = client.post(
        "/api/v1/auth/oauth/github",
        json={"provider": "github", "email": f"gh_{uuid.uuid4().hex[:8]}@github.com", "name": "Octocat"},
    )
    assert github_resp.status_code == 200
    assert github_resp.json()["user"]["provider"] == "github"

    # 5. List conversations
    conv_resp = client.get("/api/v1/conversations", headers=headers)
    assert conv_resp.status_code == 200
    assert isinstance(conv_resp.json(), list)
