from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class QuestionCategory(str, Enum):
    SELECT_FILTER = "Select & Filtering"
    BASIC_JOINS = "Basic Joins"
    AGGREGATION = "Aggregation & Grouping"
    SORTING_GROUPING = "Sorting & Grouping"
    ADVANCED_JOINS = "Advanced Joins"
    SUBQUERIES_WINDOW = "Subqueries & Window Functions"


class QuestionSummary(BaseModel):
    id: str
    number: int
    title: str
    difficulty: Difficulty
    category: QuestionCategory
    acceptance_rate: str
    is_solved: bool = False


class QuestionDetail(BaseModel):
    id: str
    number: int
    title: str
    difficulty: Difficulty
    category: QuestionCategory
    acceptance_rate: str
    layman_description: str
    tables_used: list[str]
    starter_code: str
    expected_columns: list[str]
    layman_explanation: str
    time_efficiency_tip: str
    memory_efficiency_tip: str
    is_solved: bool = False


class RunCodeRequest(BaseModel):
    question_id: str
    sql: str = Field(..., min_length=5, max_length=4000)


class RunCodeResponse(BaseModel):
    status: str  # "Accepted", "Wrong Answer", "Runtime Error"
    message: str
    execution_time_ms: float
    user_columns: list[str] | None = None
    user_data: list[list[Any]] | None = None
    expected_columns: list[str] | None = None
    expected_data: list[list[Any]] | None = None
    error: str | None = None


class SubmitResponse(BaseModel):
    status: str  # "Accepted", "Wrong Answer", "Runtime Error"
    message: str
    execution_time_ms: float
    is_solved: bool
    total_solved: int
    total_questions: int = 50
    user_columns: list[str] | None = None
    user_data: list[list[Any]] | None = None
    expected_columns: list[str] | None = None
    expected_data: list[list[Any]] | None = None
    error: str | None = None


class HintRequest(BaseModel):
    question_id: str
    user_sql: str | None = None
    error_message: str | None = None


class HintResponse(BaseModel):
    hint: str
    layman_analogy: str
    efficiency_pointer: str
    specific_critique: str | None = None


class SolutionRequest(BaseModel):
    question_id: str
    user_sql: str | None = None


class SolutionResponse(BaseModel):
    question_id: str
    sql: str
    explanation: str
    time_efficiency_tip: str
    memory_efficiency_tip: str


class UserProgressResponse(BaseModel):
    total_questions: int
    solved_count: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    solved_ids: list[str]
