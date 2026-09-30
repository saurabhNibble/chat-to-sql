from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_redirects_to_chat():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/chat"


def test_chat_ui_endpoint():
    response = client.get("/chat")
    assert response.status_code == 200
    assert "Text-to-SQL Clarification Engine" in response.text
    assert "chat-viewport" in response.text


def test_health_endpoints():
    for endpoint in ["/health", "/api/v1/health"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert "X-Process-Time" in response.headers


def test_query_ambiguous_flow():
    response = client.post("/api/v1/query", json={"prompt": "show me everything"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clarification_needed"
    assert data["question"] is not None
    assert isinstance(data["options"], list)


def test_query_clear_flow():
    response = client.post("/api/v1/query", json={"prompt": "show customers"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["generated_sql"] is not None
    assert isinstance(data["columns"], list)
    assert isinstance(data["data"], list)


def test_query_invalid_payload():
    response = client.post("/api/v1/query", json={})
    assert response.status_code == 422


def test_query_multi_turn_clarification_flow():
    # Turn 1: Send ambiguous prompt
    r1 = client.post("/api/v1/query", json={"prompt": "show top 5"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["status"] == "clarification_needed"
    conv_id = d1["conversation_id"]
    assert conv_id is not None

    # Turn 2: User responds with "customers" using same conversation_id
    r2 = client.post("/api/v1/query", json={"prompt": "customers", "conversation_id": conv_id})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["status"] == "success"
    assert "customers" in d2["generated_sql"].lower()
    assert d2["conversation_id"] == conv_id


def test_query_general_conceptual_flow():
    # Ask a conceptual SQL question
    resp = client.post("/api/v1/query", json={"prompt": "What is a JOIN in SQL?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "general_response"
    assert data["explanation"] is not None
    assert len(data["explanation"]) > 10
