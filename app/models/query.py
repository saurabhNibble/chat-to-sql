from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QueryStatus(str, Enum):
    SUCCESS = "success"
    CLARIFICATION_NEEDED = "clarification_needed"
    GENERAL_RESPONSE = "general_response"
    ERROR = "error"


class QueryRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The natural language question or instruction to convert to SQL.",
        examples=["Show top 5 customers by signup date", "List all product categories"],
    )
    conversation_id: str | None = Field(
        default=None,
        description="Optional session UUID to maintain conversation state across clarification questions.",
        examples=["a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"],
    )


class QueryResponse(BaseModel):
    status: QueryStatus = Field(
        ...,
        description="Outcome of the query analysis and execution.",
        examples=[QueryStatus.SUCCESS],
    )
    conversation_id: str | None = Field(
        default=None,
        description="Conversation session ID for subsequent follow-up interactions.",
        examples=["a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"],
    )
    question: str | None = Field(
        default=None,
        description="Clarification question when the prompt is ambiguous.",
        examples=["Which table would you like to query?"],
    )
    options: list[str] | None = Field(
        default=None,
        description="Candidate table or entity options to resolve ambiguity.",
        examples=[["customers", "orders", "products"]],
    )
    generated_sql: str | None = Field(
        default=None,
        description="The verified, safe read-only SQL query executed.",
        examples=["SELECT customer_id, name, email FROM customers LIMIT 10;"],
    )
    columns: list[str] | None = Field(
        default=None,
        description="Column headers returned from the executed query.",
        examples=[["customer_id", "name", "email"]],
    )
    data: list[list[Any]] | None = Field(
        default=None,
        description="Tabular row results returned by the database.",
    )
    row_count: int | None = Field(
        default=None,
        description="Total number of rows returned in this response.",
        examples=[5],
    )
    execution_time_ms: float | None = Field(
        default=None,
        description="Total execution time in milliseconds.",
        examples=[12.4],
    )
    explanation: str | None = Field(
        default=None,
        description="Informational or educational response for general SQL questions and greetings.",
        examples=["A JOIN clause is used to combine rows from two or more tables based on a related column."],
    )
    time_efficiency_tip: str | None = Field(
        default=None,
        description="Guidance on index utilization, algorithmic runtime, and execution speed.",
        examples=["Use an index on customer_id to avoid O(N) full table scan."],
    )
    memory_efficiency_tip: str | None = Field(
        default=None,
        description="Guidance on RAM usage, buffer pools, and preventing memory-heavy joins or sorts.",
        examples=["Keep rows small by projecting only required columns and streaming with LIMIT."],
    )


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health indicator", examples=["ok"])
    database: str = Field(..., description="Database connectivity status", examples=["connected"])
    version: str = Field(..., description="API version", examples=["1.0.0"])


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error description")
    error_code: str | None = Field(default=None, description="Standardized error code")
