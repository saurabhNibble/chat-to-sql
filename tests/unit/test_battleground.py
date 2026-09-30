from app.data.sql_questions import TOP_50_SQL_QUESTIONS
from app.services.battleground import BattlegroundService


def test_battleground_questions_count():
    assert len(TOP_50_SQL_QUESTIONS) == 50
    svc = BattlegroundService()
    questions = svc.list_questions()
    assert len(questions) == 50


def test_battleground_filter_difficulty():
    svc = BattlegroundService()
    easy_q = svc.list_questions(difficulty="Easy")
    assert len(easy_q) > 0
    assert all(q.difficulty.value == "Easy" for q in easy_q)


def test_battleground_filter_category():
    svc = BattlegroundService()
    joins_q = svc.list_questions(category="Basic Joins")
    assert len(joins_q) > 0
    assert all(q.category.value == "Basic Joins" for q in joins_q)


def test_battleground_get_detail():
    svc = BattlegroundService()
    detail = svc.get_question("1-high-value-products")
    assert detail is not None
    assert detail.number == 1
    assert "products" in detail.tables_used
    assert detail.layman_explanation != ""
    assert detail.time_efficiency_tip != ""
    assert detail.memory_efficiency_tip != ""


def test_battleground_run_and_submit():
    svc = BattlegroundService()
    # Test valid query
    valid_sql = "SELECT product_id, product_name, category, price FROM products WHERE price > 450 ORDER BY price DESC LIMIT 5;"
    run_res = svc.run_code("1-high-value-products", valid_sql)
    assert run_res.status == "Accepted"
    assert run_res.user_data is not None
    assert len(run_res.user_data) > 0

    sub_res = svc.submit_code("1-high-value-products", valid_sql)
    assert sub_res.status == "Accepted"
    assert sub_res.is_solved is True

    # Test wrong answer
    wrong_sql = "SELECT product_id, product_name, category, price FROM products WHERE price < 10 ORDER BY price ASC LIMIT 5;"
    wrong_res = svc.run_code("1-high-value-products", wrong_sql)
    assert wrong_res.status == "Wrong Answer"

    # Test rejected unsafe query
    unsafe_sql = "DROP TABLE products;"
    unsafe_res = svc.run_code("1-high-value-products", unsafe_sql)
    assert unsafe_res.status == "Runtime Error"
