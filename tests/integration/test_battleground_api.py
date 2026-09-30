import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_battleground_api_list_and_filters():
    # 1. List all questions
    resp = client.get("/api/v1/battleground/questions")
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) == 50

    # 2. Filter by difficulty
    resp_easy = client.get("/api/v1/battleground/questions?difficulty=Easy")
    assert resp_easy.status_code == 200
    easy_questions = resp_easy.json()
    assert len(easy_questions) > 0
    assert all(q["difficulty"] == "Easy" for q in easy_questions)

    # 3. Filter by category
    resp_cat = client.get("/api/v1/battleground/questions?category=Basic Joins")
    assert resp_cat.status_code == 200
    joins_questions = resp_cat.json()
    assert len(joins_questions) > 0
    assert all(q["category"] == "Basic Joins" for q in joins_questions)

    # 4. Search keyword
    resp_search = client.get("/api/v1/battleground/questions?search=products")
    assert resp_search.status_code == 200
    search_questions = resp_search.json()
    assert len(search_questions) > 0


def test_battleground_api_get_detail():
    # Valid question
    resp = client.get("/api/v1/battleground/questions/1-high-value-products")
    assert resp.status_code == 200
    q = resp.json()
    assert q["id"] == "1-high-value-products"
    assert q["number"] == 1
    assert "products" in q["tables_used"]
    assert "layman_explanation" in q and len(q["layman_explanation"]) > 10
    assert q["time_efficiency_tip"]
    assert q["memory_efficiency_tip"]
    assert q["starter_code"]

    # Invalid question 404
    resp_404 = client.get("/api/v1/battleground/questions/invalid-question-id-999")
    assert resp_404.status_code == 404


def test_battleground_api_run_and_submit_flow():
    # Run code - correct
    valid_sql = "SELECT product_id, product_name, category, price FROM products WHERE price > 450 ORDER BY price DESC LIMIT 5;"
    run_resp = client.post(
        "/api/v1/battleground/run",
        json={"question_id": "1-high-value-products", "sql": valid_sql},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "Accepted"
    assert run_data["execution_time_ms"] >= 0
    assert len(run_data["user_data"]) > 0

    # Run code - wrong answer
    wrong_sql = "SELECT product_id, product_name, category, price FROM products WHERE price < 10 ORDER BY price ASC LIMIT 5;"
    wrong_resp = client.post(
        "/api/v1/battleground/run",
        json={"question_id": "1-high-value-products", "sql": wrong_sql},
    )
    assert wrong_resp.status_code == 200
    wrong_data = wrong_resp.json()
    assert wrong_data["status"] == "Wrong Answer"

    # Run code - dangerous statement blocked
    danger_resp = client.post(
        "/api/v1/battleground/run",
        json={"question_id": "1-high-value-products", "sql": "DROP TABLE products;"},
    )
    assert danger_resp.status_code == 200
    danger_data = danger_resp.json()
    assert danger_data["status"] == "Runtime Error"

    # Authenticated user submission with unique email
    unique_email = f"bg_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Battleground Champ",
            "email": unique_email,
            "password": "Password123!",
        },
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Submit valid solution
    sub_resp = client.post(
        "/api/v1/battleground/submit",
        json={"question_id": "1-high-value-products", "sql": valid_sql},
        headers=headers,
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert sub_data["status"] == "Accepted"
    assert sub_data["is_solved"] is True

    # Check progress
    prog_resp = client.get("/api/v1/battleground/progress", headers=headers)
    assert prog_resp.status_code == 200
    prog_data = prog_resp.json()
    assert prog_data["total_questions"] == 50
    assert prog_data["solved_count"] >= 1
    assert prog_data["easy_solved"] >= 1


def test_battleground_api_hint():
    resp = client.post(
        "/api/v1/battleground/hint",
        json={
            "question_id": "1-high-value-products",
            "user_sql": "SELECT * FROM products;",
        },
    )
    assert resp.status_code == 200
    hint_data = resp.json()
    assert "hint" in hint_data
    assert "layman_analogy" in hint_data
    assert "efficiency_pointer" in hint_data


def test_battleground_api_hint_with_error():
    resp = client.post(
        "/api/v1/battleground/hint",
        json={
            "question_id": "1-high-value-products",
            "user_sql": "SELECT product_name FROM products WHERE ;",
            "error_message": "Incomplete SQL: Your WHERE clause is missing a condition expression (e.g., 'WHERE price > 450').",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "hint" in data
    assert "layman_analogy" in data
    assert "efficiency_pointer" in data


def test_battleground_api_solution():
    resp = client.post(
        "/api/v1/battleground/solution",
        json={
            "question_id": "1-high-value-products",
            "user_sql": "SELECT product_id, product_name, category, price FROM products;",
        },
    )
    assert resp.status_code == 200
    sol_data = resp.json()
    assert sol_data["question_id"] == "1-high-value-products"
    assert "sql" in sol_data and "SELECT" in sol_data["sql"]
    assert "explanation" in sol_data and len(sol_data["explanation"]) > 0
    assert "time_efficiency_tip" in sol_data
    assert "memory_efficiency_tip" in sol_data

