import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.core.logging import logger

DB_DIR = Path("data")
DB_PATH = DB_DIR / "auth_and_history.db"


def _get_history_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@dataclass
class ConversationState:
    conversation_id: str
    user_id: str | None = None
    title: str = "New Chat"
    messages: list[dict[str, str]] = field(default_factory=list)
    pending_prompt: str | None = None
    last_clarification_question: str | None = None
    last_options: list[str] | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class ConversationStore:
    """Hybrid in-memory cache and persistent SQLite conversation manager."""

    def __init__(self, ttl_seconds: int = 3600, max_conversations: int = 1000):
        self._conversations: dict[str, ConversationState] = {}
        self.ttl_seconds = ttl_seconds
        self.max_conversations = max_conversations
        self._init_db()

    def _init_db(self) -> None:
        try:
            with _get_history_db() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        title TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata_json TEXT,
                        created_at REAL NOT NULL,
                        FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                    );
                    """
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Could not initialize conversation history tables: {exc}")

    def get_or_create(
        self,
        conversation_id: str | None = None,
        user_id: str | None = None,
    ) -> ConversationState:
        self.cleanup_expired()

        if conversation_id and conversation_id in self._conversations:
            state = self._conversations[conversation_id]
            state.updated_at = time.time()
            if user_id and not state.user_id:
                state.user_id = user_id
                self._update_session_user_in_db(state.conversation_id, user_id)
            return state

        # If conversation_id is provided, try loading from DB
        if conversation_id:
            db_state = self._load_from_db(conversation_id)
            if db_state:
                if user_id and not db_state.user_id:
                    db_state.user_id = user_id
                    self._update_session_user_in_db(db_state.conversation_id, user_id)
                self._conversations[conversation_id] = db_state
                return db_state

        new_id = conversation_id or str(uuid.uuid4())
        now = time.time()
        state = ConversationState(
            conversation_id=new_id,
            user_id=user_id,
            title="New Chat",
            created_at=now,
            updated_at=now,
        )

        if len(self._conversations) >= self.max_conversations:
            oldest_id = min(self._conversations, key=lambda k: self._conversations[k].updated_at)
            del self._conversations[oldest_id]

        self._conversations[new_id] = state
        self._persist_session(state)
        return state

    def resolve_prompt(self, state: ConversationState, new_prompt: str) -> str:
        clean_input = new_prompt.strip()

        if state.pending_prompt and state.last_options:
            matched_option = next(
                (opt for opt in state.last_options if opt.lower() in clean_input.lower()),
                None,
            )
            if matched_option:
                resolved = f"{state.pending_prompt} from {matched_option}"
                state.pending_prompt = None
                state.last_clarification_question = None
                state.last_options = None
                return resolved

        return clean_input

    def record_turn(
        self,
        state: ConversationState,
        user_prompt: str,
        assistant_response: str,
        clarification_needed: bool = False,
        clarification_question: str | None = None,
        options: list[str] | None = None,
        metadata: dict | None = None,
    ) -> None:
        now = time.time()
        state.messages.append({"role": "user", "content": user_prompt})
        state.messages.append({"role": "assistant", "content": assistant_response})
        state.updated_at = now

        # Update title from the first prompt if still default
        if state.title == "New Chat":
            clean_title = user_prompt.strip()
            if len(clean_title) > 35:
                clean_title = clean_title[:32] + "..."
            state.title = clean_title.capitalize()

        if clarification_needed:
            state.pending_prompt = user_prompt
            state.last_clarification_question = clarification_question
            state.last_options = options
        else:
            state.pending_prompt = None
            state.last_clarification_question = None
            state.last_options = None

        # Persist session & messages
        self._persist_session(state)
        self._persist_message(state.conversation_id, "user", user_prompt, None, now)
        self._persist_message(state.conversation_id, "assistant", assistant_response, metadata, now)

    def _persist_session(self, state: ConversationState) -> None:
        try:
            with _get_history_db() as conn:
                conn.execute(
                    """
                    INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        user_id = excluded.user_id,
                        title = excluded.title,
                        updated_at = excluded.updated_at
                    """,
                    (state.conversation_id, state.user_id, state.title, state.created_at, state.updated_at),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Error persisting chat session {state.conversation_id}: {exc}")

    def _update_session_user_in_db(self, conversation_id: str, user_id: str) -> None:
        try:
            with _get_history_db() as conn:
                conn.execute(
                    "UPDATE chat_sessions SET user_id = ? WHERE id = ?",
                    (user_id, conversation_id),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Error updating session user in DB: {exc}")

    def _persist_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None,
        created_at: float,
    ) -> None:
        try:
            meta_str = json.dumps(metadata) if metadata else None
            with _get_history_db() as conn:
                conn.execute(
                    """
                    INSERT INTO chat_messages (session_id, role, content, metadata_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (session_id, role, content, meta_str, created_at),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Error persisting chat message for session {session_id}: {exc}")

    def _load_from_db(self, conversation_id: str) -> ConversationState | None:
        try:
            with _get_history_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, user_id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
                    (conversation_id,),
                )
                sess_row = cursor.fetchone()
                if not sess_row:
                    return None

                cursor.execute(
                    "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
                    (conversation_id,),
                )
                msg_rows = cursor.fetchall()
                messages = [{"role": r["role"], "content": r["content"]} for r in msg_rows]

                return ConversationState(
                    conversation_id=sess_row["id"],
                    user_id=sess_row["user_id"],
                    title=sess_row["title"],
                    messages=messages,
                    created_at=sess_row["created_at"],
                    updated_at=sess_row["updated_at"],
                )
        except Exception as exc:
            logger.warning(f"Error loading session {conversation_id} from DB: {exc}")
            return None

    def list_conversations(self, user_id: str | None = None, limit: int = 50) -> list[dict]:
        try:
            with _get_history_db() as conn:
                cursor = conn.cursor()
                if user_id:
                    cursor.execute(
                        """
                        SELECT s.id, s.title, s.created_at, s.updated_at, COUNT(m.id) as message_count
                        FROM chat_sessions s
                        LEFT JOIN chat_messages m ON s.id = m.session_id
                        WHERE s.user_id = ?
                        GROUP BY s.id
                        ORDER BY s.updated_at DESC
                        LIMIT ?
                        """,
                        (user_id, limit),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT s.id, s.title, s.created_at, s.updated_at, COUNT(m.id) as message_count
                        FROM chat_sessions s
                        LEFT JOIN chat_messages m ON s.id = m.session_id
                        GROUP BY s.id
                        ORDER BY s.updated_at DESC
                        LIMIT ?
                        """,
                        (limit,),
                    )

                rows = cursor.fetchall()
                return [
                    {
                        "id": r["id"],
                        "title": r["title"],
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                        "message_count": r["message_count"],
                    }
                    for r in rows
                ]
        except Exception as exc:
            logger.warning(f"Error listing conversations from DB: {exc}")
            return []

    def get_conversation_history(self, conversation_id: str) -> dict | None:
        try:
            with _get_history_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, user_id, title, created_at, updated_at FROM chat_sessions WHERE id = ?",
                    (conversation_id,),
                )
                session = cursor.fetchone()
                if not session:
                    return None

                cursor.execute(
                    """
                    SELECT id, role, content, metadata_json, created_at
                    FROM chat_messages
                    WHERE session_id = ?
                    ORDER BY id ASC
                    """,
                    (conversation_id,),
                )
                messages = []
                for m in cursor.fetchall():
                    meta = json.loads(m["metadata_json"]) if m["metadata_json"] else None
                    messages.append({
                        "id": m["id"],
                        "role": m["role"],
                        "content": m["content"],
                        "metadata": meta,
                        "created_at": m["created_at"],
                    })

                return {
                    "id": session["id"],
                    "user_id": session["user_id"],
                    "title": session["title"],
                    "created_at": session["created_at"],
                    "updated_at": session["updated_at"],
                    "messages": messages,
                }
        except Exception as exc:
            logger.warning(f"Error fetching conversation history {conversation_id}: {exc}")
            return None

    def delete_conversation(self, conversation_id: str, user_id: str | None = None) -> bool:
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]

        try:
            with _get_history_db() as conn:
                if user_id:
                    conn.execute("DELETE FROM chat_sessions WHERE id = ? AND user_id = ?", (conversation_id, user_id))
                else:
                    conn.execute("DELETE FROM chat_sessions WHERE id = ?", (conversation_id,))
                conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (conversation_id,))
                conn.commit()
                return True
        except Exception as exc:
            logger.warning(f"Error deleting conversation {conversation_id}: {exc}")
            return False

    def clear_all(self, user_id: str | None = None) -> None:
        self._conversations.clear()
        try:
            with _get_history_db() as conn:
                if user_id:
                    conn.execute(
                        "DELETE FROM chat_messages WHERE session_id IN (SELECT id FROM chat_sessions WHERE user_id = ?)",
                        (user_id,),
                    )
                    conn.execute("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
                else:
                    conn.execute("DELETE FROM chat_messages")
                    conn.execute("DELETE FROM chat_sessions")
                conn.commit()
        except Exception as exc:
            logger.warning(f"Error clearing conversation history: {exc}")

    def cleanup_expired(self) -> None:
        now = time.time()
        expired = [
            cid
            for cid, state in self._conversations.items()
            if (now - state.updated_at) > self.ttl_seconds
        ]
        for cid in expired:
            del self._conversations[cid]


conversation_store = ConversationStore()
