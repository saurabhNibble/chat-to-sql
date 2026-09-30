import re
from dataclasses import dataclass


@dataclass
class ClarificationResult:
    is_ambiguous: bool
    clarification_question: str | None = None
    options: list[str] | None = None


class ClarificationService:
    @staticmethod
    def _matches_table(prompt: str, table_name: str) -> bool:
        prompt_lower = prompt.lower()
        table_lower = table_name.lower()

        # Direct substring
        if table_lower in prompt_lower:
            return True

        # Underscore replaced with space
        spaced = table_lower.replace("_", " ")
        if spaced in prompt_lower:
            return True

        # Handle simple plurals / singulars (e.g. "order" vs "orders", "customer" vs "customers")
        if table_lower.endswith("s") and table_lower[:-1] in prompt_lower:
            return True
        if not table_lower.endswith("s") and f"{table_lower}s" in prompt_lower:
            return True

        # Regex word boundary check
        tokens = re.findall(r"\b\w+\b", prompt_lower)
        if table_lower in tokens or (table_lower.endswith("s") and table_lower[:-1] in tokens):
            return True

        return False

    @classmethod
    def classify_intent(cls, prompt: str, schema: dict[str, list[str]]) -> str:
        """
        Classifies user prompt into either 'DATA_QUERY' or 'GENERAL_CHAT'.
        Uses high-precision heuristics followed by LLM classification when necessary.
        """
        p = (prompt or "").strip().lower()
        if not p:
            return "GENERAL_CHAT"

        # 1. High-priority conversational & educational triggers
        chat_keywords = [
            "interview", "question", "questions", "practice", "quiz",
            "explain", "difference", "teach", "learn", "study", "tip", "tips",
            "what is", "what are", "how does", "how to", "why is", "tell me about",
            "hello", "hi", "hey", "i am", "my name", "who are you",
            "what can you do", "help", "thanks", "thank you", "bye", "good morning",
            "meaning of", "syntax of", "advice", "suggest"
        ]
        if any(re.search(rf"\b{re.escape(kw)}\b", p) for kw in chat_keywords):
            return "GENERAL_CHAT"

        # 2. Direct database queries: table names or query verbs
        query_verbs = [
            "select", "show", "list", "get", "fetch", "find", "display",
            "count", "calculate", "sum", "average", "avg", "top", "max", "min",
            "records", "everything", "all"
        ]
        if any(cls._matches_table(prompt, t) for t in schema.keys()) or any(re.search(rf"\b{v}\b", p) for v in query_verbs):
            return "DATA_QUERY"

        # 3. If an LLM is active, use it for ambiguous boundary phrases
        from app.core.config import get_settings
        settings = get_settings()
        api_key = settings.active_llm_api_key

        if api_key and not api_key.startswith("your_"):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url=settings.LLM_BASE_URL)
                system_prompt = (
                    "You are an intent classifier for a database assistant.\n"
                    f"Available database tables: {', '.join(schema.keys())}.\n\n"
                    "Classify prompt as either:\n"
                    "- 'DATA_QUERY': if user explicitly wants to fetch, filter, aggregate, or look up rows/data from database tables.\n"
                    "- 'GENERAL_CHAT': if user is greeting, introducing themselves, asking general or conceptual SQL questions, asking for interview practice, asking for advice, or chatting.\n\n"
                    "Output JSON only: {\"intent\": \"DATA_QUERY\" | \"GENERAL_CHAT\"}"
                )
                res = client.chat.completions.create(
                    model=settings.active_llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.0,
                    max_tokens=30,
                )
                content = res.choices[0].message.content or ""
                if "DATA_QUERY" in content:
                    return "DATA_QUERY"
                if "GENERAL_CHAT" in content:
                    return "GENERAL_CHAT"
            except Exception:
                pass

        return "GENERAL_CHAT"

    @classmethod
    def is_general_or_conceptual(cls, prompt: str, schema: dict[str, list[str]] | None = None) -> bool:
        """Convenience method for backward compatibility."""
        return cls.classify_intent(prompt, schema or {}) == "GENERAL_CHAT"

    @classmethod
    def check_clarification(cls, prompt: str, schema: dict[str, list[str]]) -> ClarificationResult:
        """
        Evaluate if a user prompt is ambiguous given the active database schema.
        """
        if not schema:
            return ClarificationResult(is_ambiguous=False)

        tables = list(schema.keys())
        if len(tables) <= 1:
            return ClarificationResult(is_ambiguous=False)

        prompt_clean = (prompt or "").strip()
        if not prompt_clean:
            return ClarificationResult(
                is_ambiguous=True,
                clarification_question="What data would you like to retrieve?",
                options=sorted(tables),
            )

        matched_tables = [table for table in tables if cls._matches_table(prompt_clean, table)]

        # If no tables are referenced and the schema has multiple choices
        if not matched_tables:
            return ClarificationResult(
                is_ambiguous=True,
                clarification_question="Which table would you like to query?",
                options=sorted(tables),
            )

        # If multiple unrelated tables are mentioned ambiguously
        if len(matched_tables) > 1 and len(set(matched_tables)) > 1:
            return ClarificationResult(
                is_ambiguous=True,
                clarification_question="Your query references multiple entities. Which primary table did you want?",
                options=sorted(matched_tables),
            )

        return ClarificationResult(is_ambiguous=False)


def check_clarification(prompt: str, schema: dict[str, list[str]]) -> ClarificationResult:
    """Convenience functional wrapper."""
    return ClarificationService.check_clarification(prompt, schema)
