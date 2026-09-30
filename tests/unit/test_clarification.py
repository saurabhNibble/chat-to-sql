from app.services.clarification import ClarificationService


def test_clarification_no_tables_in_schema():
    schema = {}
    result = ClarificationService.check_clarification("show customers", schema)
    assert not result.is_ambiguous


def test_clarification_single_table_schema():
    schema = {"customers": ["id", "name"]}
    result = ClarificationService.check_clarification("give me data", schema)
    assert not result.is_ambiguous


def test_clarification_ambiguous_prompt_no_table_mentioned():
    schema = {
        "customers": ["id", "name"],
        "orders": ["id", "total"],
        "products": ["id", "price"],
    }
    result = ClarificationService.check_clarification("give me everything", schema)
    assert result.is_ambiguous
    assert result.options == ["customers", "orders", "products"]
    assert "Which table" in result.clarification_question


def test_clarification_clear_prompt_single_table_mentioned():
    schema = {
        "customers": ["id", "name"],
        "orders": ["id", "total"],
    }
    result = ClarificationService.check_clarification("show all customers", schema)
    assert not result.is_ambiguous


def test_clarification_plural_singular_matching():
    schema = {
        "orders": ["id", "total"],
        "products": ["id", "price"],
    }
    result = ClarificationService.check_clarification("find an order by id", schema)
    assert not result.is_ambiguous


def test_clarification_multiple_tables_mentioned():
    schema = {
        "customers": ["id", "name"],
        "orders": ["id", "total"],
        "products": ["id", "price"],
    }
    result = ClarificationService.check_clarification("compare customers and products", schema)
    assert result.is_ambiguous
    assert set(result.options) == {"customers", "products"}


def test_is_general_or_conceptual():
    # Greetings
    assert ClarificationService.is_general_or_conceptual("hello")
    assert ClarificationService.is_general_or_conceptual("hi there")
    assert ClarificationService.is_general_or_conceptual("what can you do")

    # Conceptual SQL questions
    assert ClarificationService.is_general_or_conceptual("what is a join?")
    assert ClarificationService.is_general_or_conceptual("explain difference between where and having")
    assert ClarificationService.is_general_or_conceptual("how does an index work?")
    assert ClarificationService.is_general_or_conceptual("tell me about primary keys")

    # Real data queries should NOT be conceptual
    assert not ClarificationService.is_general_or_conceptual("show customers")
    assert not ClarificationService.is_general_or_conceptual("list top 5 products")
