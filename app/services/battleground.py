import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import logger
from app.data.sql_questions import TOP_50_SQL_QUESTIONS
from app.db.schema import execute_readonly_sql
from app.models.battleground import (
    Difficulty,
    HintResponse,
    QuestionCategory,
    QuestionDetail,
    QuestionSummary,
    RunCodeResponse,
    SolutionResponse,
    SubmitResponse,
    UserProgressResponse,
)
from app.services.sql_generator import SqlGeneratorService
from app.services.sql_validator import SqlValidator

settings = get_settings()

DB_DIR = Path("data")
DB_PATH = DB_DIR / "auth_and_history.db"


def _get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


class BattlegroundService:
    def __init__(self):
        self.validator = SqlValidator()
        self.questions_by_id = {q["id"]: q for q in TOP_50_SQL_QUESTIONS}
        self._init_db()

    def _init_db(self) -> None:
        try:
            with _get_db() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS battleground_submissions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        question_id TEXT NOT NULL,
                        submitted_sql TEXT NOT NULL,
                        status TEXT NOT NULL,
                        execution_time_ms REAL NOT NULL,
                        created_at REAL NOT NULL
                    );
                    """
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Error initializing battleground_submissions table: {exc}")

    def _get_solved_ids(self, user_id: str | None = None) -> set[str]:
        try:
            with _get_db() as conn:
                cursor = conn.cursor()
                if user_id:
                    cursor.execute(
                        "SELECT DISTINCT question_id FROM battleground_submissions WHERE user_id = ? AND status = 'Accepted'",
                        (user_id,),
                    )
                else:
                    cursor.execute(
                        "SELECT DISTINCT question_id FROM battleground_submissions WHERE status = 'Accepted'"
                    )
                return {r["question_id"] for r in cursor.fetchall()}
        except Exception as exc:
            logger.warning(f"Error retrieving solved questions: {exc}")
            return set()

    def list_questions(
        self,
        user_id: str | None = None,
        difficulty: str | None = None,
        category: str | None = None,
        search: str | None = None,
    ) -> list[QuestionSummary]:
        solved_ids = self._get_solved_ids(user_id)
        results = []

        search_clean = (search or "").strip().lower()

        for q in TOP_50_SQL_QUESTIONS:
            if difficulty and q["difficulty"].lower() != difficulty.lower():
                continue
            if category and q["category"].lower() != category.lower():
                continue
            if search_clean and search_clean not in q["title"].lower() and search_clean not in q["layman_description"].lower():
                continue

            results.append(
                QuestionSummary(
                    id=q["id"],
                    number=q["number"],
                    title=q["title"],
                    difficulty=Difficulty(q["difficulty"]),
                    category=QuestionCategory(q["category"]),
                    acceptance_rate=q["acceptance_rate"],
                    is_solved=q["id"] in solved_ids,
                )
            )

        return results

    def get_question(self, question_id: str, user_id: str | None = None) -> QuestionDetail | None:
        q = self.questions_by_id.get(question_id)
        if not q:
            return None

        solved_ids = self._get_solved_ids(user_id)

        # Get expected columns by inspecting reference query
        try:
            expected_cols, _ = execute_readonly_sql(q["expected_query"])
        except Exception:
            expected_cols = ["result"]

        return QuestionDetail(
            id=q["id"],
            number=q["number"],
            title=q["title"],
            difficulty=Difficulty(q["difficulty"]),
            category=QuestionCategory(q["category"]),
            acceptance_rate=q["acceptance_rate"],
            layman_description=q["layman_description"],
            tables_used=q["tables_used"],
            starter_code=q["starter_code"],
            expected_columns=expected_cols,
            layman_explanation=q["layman_explanation"],
            time_efficiency_tip=q["time_efficiency_tip"],
            memory_efficiency_tip=q["memory_efficiency_tip"],
            is_solved=q["id"] in solved_ids,
        )

    def _normalize_cell(self, val: Any) -> str:
        if val is None:
            return ""
        try:
            f = float(val)
            return f"{f:.4f}"
        except (ValueError, TypeError):
            return str(val).strip()

    def _compare_results(
        self,
        user_rows: list[list],
        expected_rows: list[list],
    ) -> tuple[bool, str]:
        """Compares result sets for semantic equality with tie-order resilience."""
        if len(user_rows) != len(expected_rows):
            return False, f"Row count mismatch: expected {len(expected_rows)} row(s), but your query returned {len(user_rows)}."

        if not user_rows and not expected_rows:
            return True, "Accepted"

        if len(user_rows[0]) != len(expected_rows[0]):
            return False, f"Column count mismatch: expected {len(expected_rows[0])} column(s), but your query returned {len(user_rows[0])}."

        # 1. First attempt: Direct row-by-row ordered comparison
        direct_match = True
        first_mismatch_msg = ""
        for i, (u_row, exp_row) in enumerate(zip(user_rows, expected_rows, strict=True)):
            for j, (u_val, exp_val) in enumerate(zip(u_row, exp_row, strict=True)):
                u_norm = self._normalize_cell(u_val)
                exp_norm = self._normalize_cell(exp_val)
                if u_norm != exp_norm:
                    direct_match = False
                    first_mismatch_msg = f"Mismatch at row {i + 1}, column {j + 1}: expected '{exp_norm}', got '{u_norm}'."
                    break
            if not direct_match:
                break

        if direct_match:
            return True, "Accepted"

        # 2. Second attempt: Multiset equivalence (handles database engine tie-breaking variance)
        user_bag = sorted(tuple(self._normalize_cell(v) for v in r) for r in user_rows)
        exp_bag = sorted(tuple(self._normalize_cell(v) for v in r) for r in expected_rows)

        if user_bag == exp_bag:
            return True, "Accepted"

        return False, first_mismatch_msg

    def run_code(self, question_id: str, sql: str) -> RunCodeResponse:
        q = self.questions_by_id.get(question_id)
        if not q:
            return RunCodeResponse(
                status="Runtime Error",
                message="Question not found.",
                execution_time_ms=0,
                error="Invalid question ID",
            )

        # 1. AST Safety Check
        is_safe, reason = self.validator.validate_query(sql)
        if not is_safe:
            clean_reason = re.sub(r"\x1b\[[0-9;]*[mK]", "", reason or "")
            return RunCodeResponse(
                status="Runtime Error",
                message=f"Query rejected: {clean_reason}",
                execution_time_ms=0,
                error=clean_reason,
            )

        start_time = time.perf_counter()

        # 2. Run Expected Query
        try:
            exp_cols, exp_rows = execute_readonly_sql(q["expected_query"])
        except Exception as exc:
            clean_exp_err = re.sub(r"\x1b\[[0-9;]*[mK]", "", str(exc))
            return RunCodeResponse(
                status="Runtime Error",
                message="Error running reference solution on database.",
                execution_time_ms=0,
                error=clean_exp_err,
            )

        # 3. Run User Query
        try:
            user_cols, user_rows = execute_readonly_sql(sql)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            clean_exc = re.sub(r"\x1b\[[0-9;]*[mK]", "", str(exc))
            return RunCodeResponse(
                status="Runtime Error",
                message=f"PostgreSQL syntax or execution error: {clean_exc}",
                execution_time_ms=elapsed_ms,
                error=clean_exc,
            )

        # 4. Compare Results
        is_correct, comp_msg = self._compare_results(user_rows, exp_rows)
        status = "Accepted" if is_correct else "Wrong Answer"

        return RunCodeResponse(
            status=status,
            message=comp_msg if not is_correct else "Accepted! All test cases passed.",
            execution_time_ms=elapsed_ms,
            user_columns=user_cols,
            user_data=user_rows,
            expected_columns=exp_cols,
            expected_data=exp_rows,
        )

    def submit_code(
        self, question_id: str, sql: str, user_id: str | None = None
    ) -> SubmitResponse:
        run_res = self.run_code(question_id, sql)
        is_accepted = run_res.status == "Accepted"

        # Record submission in DB
        try:
            with _get_db() as conn:
                conn.execute(
                    """
                    INSERT INTO battleground_submissions (user_id, question_id, submitted_sql, status, execution_time_ms, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, question_id, sql, run_res.status, run_res.execution_time_ms, time.time()),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Error saving submission: {exc}")

        solved_ids = self._get_solved_ids(user_id)

        msg = (
            "Congratulations! 🎉 Your query executed flawlessly and produced the exact expected output."
            if is_accepted
            else run_res.message
        )

        return SubmitResponse(
            status=run_res.status,
            message=msg,
            execution_time_ms=run_res.execution_time_ms,
            is_solved=is_accepted,
            total_solved=len(solved_ids),
            total_questions=len(TOP_50_SQL_QUESTIONS),
            user_columns=run_res.user_columns,
            user_data=run_res.user_data,
            expected_columns=run_res.expected_columns,
            expected_data=run_res.expected_data,
            error=run_res.error,
        )

    def get_user_progress(self, user_id: str | None = None) -> UserProgressResponse:
        solved_ids = self._get_solved_ids(user_id)

        easy_count = sum(1 for q in TOP_50_SQL_QUESTIONS if q["difficulty"] == "Easy" and q["id"] in solved_ids)
        med_count = sum(1 for q in TOP_50_SQL_QUESTIONS if q["difficulty"] == "Medium" and q["id"] in solved_ids)
        hard_count = sum(1 for q in TOP_50_SQL_QUESTIONS if q["difficulty"] == "Hard" and q["id"] in solved_ids)

        return UserProgressResponse(
            total_questions=len(TOP_50_SQL_QUESTIONS),
            solved_count=len(solved_ids),
            easy_solved=easy_count,
            medium_solved=med_count,
            hard_solved=hard_count,
            solved_ids=list(solved_ids),
        )

    def get_hint(
        self,
        question_id: str,
        user_sql: str | None = None,
        error_message: str | None = None,
    ) -> HintResponse:
        q = self.questions_by_id.get(question_id)
        if not q:
            return HintResponse(
                hint="Think about the tables required and the filtering conditions.",
                layman_analogy="Break down the problem like shopping with a checklist.",
                efficiency_pointer="Use indexed columns in WHERE clauses.",
                specific_critique=None,
            )

        api_key = settings.active_llm_api_key
        if SqlGeneratorService._is_valid_api_key(api_key):
            try:
                from openai import OpenAI

                client = OpenAI(
                    api_key=api_key,
                    base_url=settings.active_llm_base_url,
                )
                prompt = (
                    f"Challenge: {q['title']}\n"
                    f"Description: {q['layman_description']}\n"
                    f"Tables used: {', '.join(q['tables_used'])}\n"
                    f"Expected Query (DO NOT REVEAL FULLY): {q['expected_query']}\n"
                    f"Learner's current SQL code:\n```sql\n{user_sql or '-- No SQL code entered yet'}\n```\n"
                )
                if error_message:
                    prompt += f"Execution error encountered: {error_message}\n"

                system_prompt = (
                    "You are an encouraging, world-class SQL coach monitoring the user's live code editor.\n"
                    "Analyze what the user wrote, find any syntax errors or logical issues, and give actionable help.\n"
                    "Output JSON ONLY:\n"
                    "{\n"
                    '  "hint": "A targeted, constructive hint telling them what to fix without revealing the full query",\n'
                    '  "analogy": "An everyday real-world analogy explaining the concept",\n'
                    '  "efficiency_pointer": "A practical speed or memory optimization tip",\n'
                    '  "critique": "1-2 sentences directly critiquing what is wrong or incomplete in their current code"\n'
                    "}"
                )
                resp = client.chat.completions.create(
                    model=settings.active_llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=450,
                )
                content = resp.choices[0].message.content or ""
                json_match = re.search(r"\{[\s\S]*\}", content)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return HintResponse(
                        hint=data.get("hint") or f"Review the conditions for '{q['title']}'.",
                        layman_analogy=data.get("analogy") or q["layman_explanation"],
                        efficiency_pointer=data.get("efficiency_pointer") or f"{q['time_efficiency_tip']} | {q['memory_efficiency_tip']}",
                        specific_critique=data.get("critique"),
                    )
            except Exception as exc:
                logger.warning(f"Gemini hint generation failed: {exc}")

        # Curated Fallback
        hint_text = (
            f"Start with a SELECT query on table '{', '.join(q['tables_used'])}'. "
            f"Check if you need a WHERE condition or GROUP BY aggregate. Remember to apply the ordering and LIMIT specified."
        )
        return HintResponse(
            hint=hint_text,
            layman_analogy=q["layman_explanation"],
            efficiency_pointer=f"{q['time_efficiency_tip']} | {q['memory_efficiency_tip']}",
            specific_critique="Make sure all clauses (SELECT, WHERE, ORDER BY) are valid and complete.",
        )

    def get_solution(
        self, question_id: str, user_sql: str | None = None
    ) -> SolutionResponse:
        q = self.questions_by_id.get(question_id)
        if not q:
            raise ValueError("Question not found.")

        api_key = settings.active_llm_api_key
        if SqlGeneratorService._is_valid_api_key(api_key):
            try:
                from openai import OpenAI

                client = OpenAI(
                    api_key=api_key,
                    base_url=settings.active_llm_base_url,
                )
                prompt = (
                    f"Challenge: {q['title']}\n"
                    f"Description: {q['layman_description']}\n"
                    f"Reference Solution: {q['expected_query']}\n"
                    f"Tables used: {', '.join(q['tables_used'])}\n"
                )
                if user_sql:
                    prompt += f"Learner's current attempt:\n```sql\n{user_sql}\n```\n"

                system_prompt = (
                    "You are an expert SQL teacher. Provide a comprehensive solution walkthrough.\n"
                    "Output JSON ONLY:\n"
                    "{\n"
                    f'  "sql": "{q["expected_query"]}",\n'
                    '  "explanation": "Clear step-by-step breakdown of how each clause works and why this is the optimal approach.",\n'
                    '  "time_efficiency": "How indexes and query planner optimize execution time.",\n'
                    '  "memory_efficiency": "How column projection and memory buffers minimize RAM usage."\n'
                    "}"
                )
                resp = client.chat.completions.create(
                    model=settings.active_llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=600,
                )
                content = resp.choices[0].message.content or ""
                json_match = re.search(r"\{[\s\S]*\}", content)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return SolutionResponse(
                        question_id=question_id,
                        sql=data.get("sql") or q["expected_query"],
                        explanation=data.get("explanation") or q["layman_explanation"],
                        time_efficiency_tip=data.get("time_efficiency") or q["time_efficiency_tip"],
                        memory_efficiency_tip=data.get("memory_efficiency") or q["memory_efficiency_tip"],
                    )
            except Exception as exc:
                logger.warning(f"Gemini solution generation failed: {exc}")

        return SolutionResponse(
            question_id=question_id,
            sql=q["expected_query"],
            explanation=q["layman_explanation"],
            time_efficiency_tip=q["time_efficiency_tip"],
            memory_efficiency_tip=q["memory_efficiency_tip"],
        )


battleground_service = BattlegroundService()
