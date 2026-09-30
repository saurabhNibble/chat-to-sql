import time

from fastapi import HTTPException

from app.core.logging import logger
from app.db.schema import execute_readonly_sql, extract_schema
from app.models.query import QueryResponse, QueryStatus
from app.services.clarification import ClarificationService
from app.services.conversation import conversation_store
from app.services.sql_generator import SqlGeneratorService
from app.services.sql_validator import SqlValidator


class QueryService:
    """Orchestrates schema extraction, multi-turn state, clarification, SQL generation, validation, and execution."""

    def __init__(self):
        self.clarification_service = ClarificationService()
        self.generator_service = SqlGeneratorService()
        self.validator = SqlValidator()
        self.conversation_store = conversation_store

    def process_query(
        self,
        prompt: str,
        conversation_id: str | None = None,
        user_id: str | None = None,
    ) -> QueryResponse:
        start_time = time.perf_counter()

        # Step 1: Manage conversation state and contextual resolution
        conv_state = self.conversation_store.get_or_create(conversation_id, user_id=user_id)
        effective_prompt = self.conversation_store.resolve_prompt(conv_state, prompt)

        # Step 2: Introspect database schema
        schema = extract_schema()
        if not schema:
            raise HTTPException(
                status_code=503,
                detail="Database schema is empty or inaccessible.",
            )

        # Step 3: Check if this is a general/conceptual SQL question or greeting
        if self.clarification_service.classify_intent(effective_prompt, schema) == "GENERAL_CHAT":
            explanation = self.generator_service.answer_conceptual_question(effective_prompt, schema)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.conversation_store.record_turn(
                conv_state,
                user_prompt=prompt,
                assistant_response=explanation,
                clarification_needed=False,
            )
            return QueryResponse(
                status=QueryStatus.GENERAL_RESPONSE,
                conversation_id=conv_state.conversation_id,
                explanation=explanation,
                execution_time_ms=elapsed_ms,
            )

        # Step 4: Ambiguity & Clarification Check for Database Queries
        clarification = self.clarification_service.check_clarification(effective_prompt, schema)
        if clarification.is_ambiguous:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(f"Clarification required for prompt: '{effective_prompt}' (conv: {conv_state.conversation_id})")
            self.conversation_store.record_turn(
                conv_state,
                user_prompt=prompt,
                assistant_response=clarification.clarification_question or "Clarification required.",
                clarification_needed=True,
                clarification_question=clarification.clarification_question,
                options=clarification.options,
            )
            return QueryResponse(
                status=QueryStatus.CLARIFICATION_NEEDED,
                conversation_id=conv_state.conversation_id,
                question=clarification.clarification_question,
                options=clarification.options,
                execution_time_ms=elapsed_ms,
            )

        # Step 5: Generate SQL with Layman explanation & Efficiency advice
        sql, layman_exp, time_tip, mem_tip = self.generator_service.generate_sql_with_explanation(
            effective_prompt, schema
        )
        logger.debug(f"Generated SQL: {sql}")

        # Step 6: Strict AST Safety Validation
        is_valid, error_reason = self.validator.validate_query(sql)
        if not is_valid:
            logger.warning(f"SQL validation rejected query '{sql}': {error_reason}")
            raise HTTPException(
                status_code=400,
                detail=f"Generated query was rejected for security policy: {error_reason}",
            )

        # Step 7: Read-only Database Execution
        try:
            columns, rows = execute_readonly_sql(sql)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(f"Query successfully executed in {elapsed_ms}ms with {len(rows)} rows returned.")
            self.conversation_store.record_turn(
                conv_state,
                user_prompt=effective_prompt,
                assistant_response=layman_exp or f"Executed query: {sql}",
                clarification_needed=False,
                metadata={
                    "sql": sql,
                    "row_count": len(rows),
                    "time_tip": time_tip,
                    "memory_tip": mem_tip,
                },
            )
            return QueryResponse(
                status=QueryStatus.SUCCESS,
                conversation_id=conv_state.conversation_id,
                generated_sql=sql,
                columns=columns,
                data=rows,
                row_count=len(rows),
                explanation=layman_exp,
                time_efficiency_tip=time_tip,
                memory_efficiency_tip=mem_tip,
                execution_time_ms=elapsed_ms,
            )
        except Exception as exc:
            logger.error(f"Execution error for query '{sql}': {exc}")
            raise HTTPException(
                status_code=500,
                detail=f"Database execution failed: {str(exc)}",
            ) from exc
