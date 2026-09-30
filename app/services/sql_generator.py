import json
import re

import sqlglot
from sqlglot import exp

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class SqlGeneratorService:
    @classmethod
    def _clean_sql(cls, raw: str) -> str:
        """Strip markdown fences, leading/trailing whitespace, and trailing semicolons."""
        cleaned = re.sub(r"^```(?:sql)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()
        if cleaned.endswith(";"):
            cleaned = cleaned[:-1].strip()
        return cleaned

    @classmethod
    def _enforce_limit(cls, sql: str) -> str:
        """Parse AST with sqlglot and enforce MAX_QUERY_LIMIT if no LIMIT is present."""
        try:
            expression = sqlglot.parse_one(sql, read="postgres")
            if expression.find(exp.Select):
                if not expression.args.get("limit"):
                    expression = expression.limit(settings.MAX_QUERY_LIMIT)
                return f"{expression.sql(dialect='postgres')};"
        except Exception:
            pass

        # Fallback regex limit injection
        if not re.search(r"\bLIMIT\s+\d+\b", sql, flags=re.IGNORECASE):
            return f"{sql} LIMIT {settings.MAX_QUERY_LIMIT};"
        return f"{sql};"

    @classmethod
    def _is_valid_api_key(cls, key: str | None) -> bool:
        if not key:
            return False
        clean = key.strip()
        if not clean or clean.startswith("your_") or "example" in clean.lower():
            return False
        return True

    @classmethod
    def _generate_with_llm(
        cls, prompt: str, schema: dict[str, list[str]]
    ) -> tuple[str | None, str | None, str | None, str | None]:
        """
        Generate SQL query with Layman explanation and Time/Memory efficiency tips.
        Returns: (sql, layman_explanation, time_efficiency_tip, memory_efficiency_tip)
        """
        api_key = settings.active_llm_api_key
        if not cls._is_valid_api_key(api_key):
            return None, None, None, None

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=api_key,
                base_url=settings.LLM_BASE_URL,
            )

            schema_lines = []
            for table, cols in schema.items():
                schema_lines.append(f"Table: {table} (Columns: {', '.join(cols)})")
            schema_context = "\n".join(schema_lines)

            system_prompt = (
                "You are an empathetic, world-class SQL mentor and database architect for learners.\n"
                "Your mission:\n"
                "1. Generate a valid, safe, read-only SELECT SQL query for the user's request.\n"
                "2. Provide an explanation in simple LAYMAN terms using everyday analogies (e.g. comparing tables to filing cabinets, rows to index cards).\n"
                "3. Provide a practical TIME efficiency suggestion (e.g. indexing, avoiding sequential scans, algorithmic speed).\n"
                "4. Provide a practical MEMORY efficiency suggestion (e.g. streaming with LIMIT, column projection, avoiding memory-hungry joins).\n\n"
                "Output JSON format ONLY:\n"
                "{\n"
                '  "sql": "SELECT ... LIMIT 10;",\n'
                '  "layman_explanation": "Imagine table as ... This query ...",\n'
                '  "time_efficiency": "Speed tip: ...",\n'
                '  "memory_efficiency": "Memory tip: ..."\n'
                "}\n\n"
                "Rules:\n"
                "- Output ONLY JSON. No text outside the JSON object.\n"
                "- Query MUST be strictly read-only SELECT or WITH.\n"
                f"- Appended LIMIT must not exceed {settings.MAX_QUERY_LIMIT}.\n"
                f"Database Schema:\n{schema_context}"
            )

            for token_limit in [550, 400]:
                try:
                    response = client.chat.completions.create(
                        model=settings.active_llm_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.1,
                        max_tokens=token_limit,
                    )

                    content = response.choices[0].message.content or ""
                    content_clean = content.strip()

                    # Try parsing JSON
                    try:
                        # Extract JSON block if wrapped
                        json_match = re.search(r"\{[\s\S]*\}", content_clean)
                        if json_match:
                            data = json.loads(json_match.group(0))
                            sql = data.get("sql")
                            if sql:
                                return (
                                    cls._clean_sql(sql),
                                    data.get("layman_explanation"),
                                    data.get("time_efficiency"),
                                    data.get("memory_efficiency"),
                                )
                    except Exception:
                        pass

                    # Fallback if raw SQL was output
                    cleaned = cls._clean_sql(content_clean)
                    if cleaned.upper().startswith("SELECT") or cleaned.upper().startswith("WITH"):
                        return cleaned, None, None, None
                except Exception as inner_exc:
                    if "rate_limit" in str(inner_exc).lower() or "429" in str(inner_exc):
                        logger.warning(f"Rate limit in generate_with_llm: {inner_exc}. Retrying with smaller window.")
                        continue
                    raise inner_exc

        except Exception as exc:
            logger.warning(
                f"LLM SQL generation with {settings.LLM_PROVIDER} ({settings.active_llm_model}) encountered an error: {exc}. "
                "Falling back to rule-based engine."
            )

        return None, None, None, None

    @classmethod
    def _generate_rule_based(
        cls, prompt: str, schema: dict[str, list[str]]
    ) -> tuple[str, str, str, str]:
        """Deterministically generate a read-only query and Layman + Efficiency guidance."""
        tables = list(schema.keys())
        if not tables:
            raise ValueError("No database schema available to generate a query.")

        prompt_lower = (prompt or "").lower()

        # Find best matching table
        selected_table = tables[0]
        for table in tables:
            table_clean = table.lower().replace("_", " ")
            if table.lower() in prompt_lower or table_clean in prompt_lower:
                selected_table = table
                break

        columns = schema.get(selected_table, [])
        if not columns:
            sql = f"SELECT * FROM {selected_table} LIMIT {settings.MAX_QUERY_LIMIT};"
            explanation = f"Imagine the '{selected_table}' table is a spreadsheet. This query takes the first {settings.MAX_QUERY_LIMIT} rows so you can inspect them without overwhelming your screen."
            time_tip = f"⚡ Time Efficiency: Reading with LIMIT {settings.MAX_QUERY_LIMIT} allows PostgreSQL to stop early instead of scanning millions of records."
            memory_tip = "💾 Memory Efficiency: Requesting only a handful of rows keeps client RAM clean and avoids large network payload transfers."
            return sql, explanation, time_tip, memory_tip

        # Check matched columns
        matched_columns = [col for col in columns if col.lower() in prompt_lower]
        select_clause = ", ".join(matched_columns) if matched_columns else "*"

        # Check for count keywords
        if any(kw in prompt_lower for kw in ["count", "how many", "total number"]):
            sql = f"SELECT COUNT(*) AS total_count FROM {selected_table};"
            explanation = f"Think of this like counting all the items on a shelf in '{selected_table}'. It returns one single tally number."
            time_tip = "⚡ Time Efficiency: A COUNT(*) can scan a lightweight primary key index in O(N) or use database statistics rather than loading entire row values."
            memory_tip = "💾 Memory Efficiency: Returns just 1 scalar number, consuming practically zero client buffer memory."
            return sql, explanation, time_tip, memory_tip

        # Check for ordering keywords
        order_clause = ""
        for col in columns:
            if "date" in col.lower() or "created" in col.lower():
                order_clause = f" ORDER BY {col} DESC"
                break

        sql = f"SELECT {select_clause} FROM {selected_table}{order_clause} LIMIT {settings.MAX_QUERY_LIMIT};"
        cols_desc = select_clause if select_clause != "*" else f"all attributes from '{selected_table}'"
        explanation = f"Imagine '{selected_table}' as an organized filing cabinet. This query opens the cabinet, pulls out {cols_desc}, and neatly hands you the top {settings.MAX_QUERY_LIMIT} records."
        time_tip = "⚡ Time Efficiency: Add a B-Tree index on any column used in 'ORDER BY' or 'WHERE' to drop search latency from O(N) table scan to O(log N) index seek."
        memory_tip = f"💾 Memory Efficiency: Limiting to {settings.MAX_QUERY_LIMIT} rows prevents large in-memory sorts (SortMethod: quicksort/quicksort in RAM) from spilling to disk temp files."
        return sql, explanation, time_tip, memory_tip

    @classmethod
    def generate_sql_with_explanation(
        cls, prompt: str, schema: dict[str, list[str]]
    ) -> tuple[str, str, str, str]:
        """Generate SQL, Layman explanation, Time efficiency tip, and Memory efficiency tip."""
        sql, explanation, time_tip, mem_tip = cls._generate_with_llm(prompt, schema)

        if not sql:
            sql, default_exp, default_time, default_mem = cls._generate_rule_based(prompt, schema)
            explanation = explanation or default_exp
            time_tip = time_tip or default_time
            mem_tip = mem_tip or default_mem
        else:
            if not explanation:
                explanation = "This query searches your database to retrieve matching records from your connected schema."
            if not time_tip:
                time_tip = "⚡ Time Efficiency: Use indexed columns in WHERE and JOIN predicates to allow PostgreSQL to seek rows directly in logarithmic time."
            if not mem_tip:
                mem_tip = "💾 Memory Efficiency: Project only the columns you need and use LIMIT to keep the working memory buffer compact."

        return cls._enforce_limit(sql), explanation, time_tip, mem_tip

    @classmethod
    def generate_sql(cls, prompt: str, schema: dict[str, list[str]]) -> str:
        """Backward compatibility wrapper returning only the verified SQL query string."""
        sql, _, _, _ = cls.generate_sql_with_explanation(prompt, schema)
        return sql

    @classmethod
    def answer_conceptual_question(cls, prompt: str, schema: dict[str, list[str]]) -> str:
        """
        Answer conceptual SQL questions, interview preparation, and general chat.
        Mandatory format: Layman terms + Time and Memory efficiency breakdown.
        """
        api_key = settings.active_llm_api_key
        table_summary = ", ".join(schema.keys()) if schema else "customers, orders, products"

        if cls._is_valid_api_key(api_key):
            try:
                from openai import OpenAI

                client = OpenAI(
                    api_key=api_key,
                    base_url=settings.LLM_BASE_URL,
                )

                system_prompt = (
                    "You are a friendly, empathetic SQL mentor and technical interview coach dedicated to learners.\n"
                    "Core Principles:\n"
                    "1. **EXPLAIN IN LAYMAN TERMS**: Use relatable everyday analogies (e.g. comparing databases to libraries, tables to spreadsheets, joins to matching socks or name tags at a meetup). Break down complex syntax simply.\n"
                    "2. **INTERVIEW & PRACTICE**: If asked for interview questions, provide realistic questions, clean code snippets, and simple explanations.\n"
                    "3. **EFFICIENCY BREAKDOWN**: Always include a dedicated performance section:\n"
                    "   ### ⚡ Performance & Efficiency Guide:\n"
                    "   - 🚀 **Time Efficiency (Speed)**: How to make it execute faster (indexes, query plan, avoiding full table scans).\n"
                    "   - 💾 **Memory Efficiency (RAM)**: How to minimize memory footprint (streaming with LIMIT, avoiding memory-heavy join bloat, filtering early).\n"
                    f"4. Connected database tables currently available: {table_summary}.\n"
                    "5. Keep the total response structured, readable in Markdown, and under 700 tokens."
                )

                for token_limit in [700, 450]:
                    try:
                        response = client.chat.completions.create(
                            model=settings.active_llm_model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt},
                            ],
                            temperature=0.3,
                            max_tokens=token_limit,
                        )
                        content = response.choices[0].message.content
                        if content and content.strip():
                            return content.strip()
                    except Exception as inner_exc:
                        if "rate_limit" in str(inner_exc).lower() or "429" in str(inner_exc):
                            logger.warning(f"Rate limit with max_tokens={token_limit}: {inner_exc}. Retrying with smaller window.")
                            continue
                        raise inner_exc
            except Exception as exc:
                logger.warning(f"Error answering conceptual question via LLM: {exc}")

        # Fallback offline explanation tailored to prompt in Layman terms + efficiency
        p_lower = prompt.lower()
        if any(w in p_lower for w in ["interview", "question", "quiz", "practice"]):
            return (
                "### 🎓 Top SQL Interview Questions (in Layman Terms)\n\n"
                "1. **`WHERE` vs `HAVING`:**\n"
                "   - *Layman Analogy:* `WHERE` is like a security guard filtering people before entering the auditorium. `HAVING` counts how many people are in each row after they sit down and only keeps rows with 5+ people.\n"
                "   - 🚀 *Time Efficiency:* Always filter with `WHERE` first to discard non-qualifying rows before expensive grouping calculations.\n\n"
                "2. **`INNER JOIN` vs `LEFT JOIN`:**\n"
                "   - *Layman Analogy:* An `INNER JOIN` is like matching pairs of socks—only matched pairs make it into the basket. A `LEFT JOIN` keeps every sock from the left drawer, pairing it up if a match exists or leaving the other side blank (`NULL`).\n"
                "   - 💾 *Memory Efficiency:* Ensure join keys (like `customer_id`) have indexes to avoid large in-memory hash join spillover.\n\n"
                "3. **What is a Common Table Expression (CTE / `WITH`)?**\n"
                "   - *Layman Analogy:* Think of a CTE as writing down a quick shopping list on a sticky note to reference during your trip. It makes complex queries readable step-by-step.\n\n"
                "4. **Window Functions (`ROW_NUMBER()` vs `RANK()`):**\n"
                "   - *Layman Analogy:* In a race, if two runners tie for 2nd place, `RANK()` gives them both 2nd and skips to 4th place. `DENSE_RANK()` gives both 2nd and names the next runner 3rd.\n\n"
                "### ⚡ General Efficiency Checklist:\n"
                "- 🚀 **Time:** Index columns used in `WHERE`, `JOIN`, and `ORDER BY` to convert full table scans into fast B-Tree seeks.\n"
                "- 💾 **Memory:** Never use `SELECT *` in production; fetch only needed columns and stream with `LIMIT`."
            )

        tables_list = "\n".join([f"- **{t}**: {', '.join(cols[:4])}..." for t, cols in schema.items()]) if schema else "- customers, orders, products"
        return (
            f"Hello! I am your **Text-to-SQL Assistant & SQL Mentor**.\n\n"
            f"I translate plain English into fast, memory-optimized SQL, and explain database concepts in **layman terms**.\n\n"
            f"**Your Active Database Tables:**\n"
            f"{tables_list}\n\n"
            f"**Try asking:**\n"
            f"- *'Show top 5 customers'* (Executes an optimized read query)\n"
            f"- *'Explain what a JOIN is in layman terms'* (Learn with simple analogies)\n"
            f"- *'Give 10 SQL interview questions'* (Practice with real examples & efficiency tips)"
        )


def generate_sql(prompt: str, schema: dict[str, list[str]]) -> str:
    """Convenience functional wrapper."""
    return SqlGeneratorService.generate_sql(prompt, schema)
