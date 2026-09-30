import hashlib
import os
import sqlite3
import time
import uuid
from pathlib import Path

import jwt

from app.models.auth import UserProfile

DB_DIR = Path("data")
DB_PATH = DB_DIR / "auth_and_history.db"

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-chatsql-jwt-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72


def _get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db() -> None:
    with _get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT,
                avatar_url TEXT,
                provider TEXT NOT NULL DEFAULT 'local',
                created_at REAL NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
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


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${pw_hash.hex()}"


def verify_password(plain_password: str, hashed: str) -> bool:
    try:
        parts = hashed.split("$")
        if len(parts) != 2:
            return False
        salt = bytes.fromhex(parts[0])
        original_hash = bytes.fromhex(parts[1])
        computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return computed == original_hash
    except Exception:
        return False


class AuthService:
    def __init__(self):
        init_auth_db()

    def create_access_token(self, user_id: str, email: str) -> str:
        payload = {
            "sub": user_id,
            "email": email,
            "exp": int(time.time()) + (JWT_EXPIRATION_HOURS * 3600),
            "iat": int(time.time()),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def decode_access_token(self, token: str) -> dict | None:
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except Exception:
            return None

    def register(self, name: str, email: str, password: str) -> tuple[UserProfile, str]:
        email_clean = email.strip().lower()
        with _get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
            if cursor.fetchone():
                raise ValueError("An account with this email already exists.")

            user_id = str(uuid.uuid4())
            now = time.time()
            pw_hash = hash_password(password)
            avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={user_id}"

            cursor.execute(
                """
                INSERT INTO users (id, email, name, password_hash, avatar_url, provider, created_at)
                VALUES (?, ?, ?, ?, ?, 'local', ?)
                """,
                (user_id, email_clean, name.strip(), pw_hash, avatar, now),
            )
            conn.commit()

        user = UserProfile(
            id=user_id,
            name=name.strip(),
            email=email_clean,
            avatar_url=avatar,
            provider="local",
            created_at=now,
        )
        token = self.create_access_token(user_id, email_clean)
        return user, token

    def login(self, email: str, password: str) -> tuple[UserProfile, str]:
        email_clean = email.strip().lower()
        with _get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, name, password_hash, avatar_url, provider, created_at FROM users WHERE email = ?",
                (email_clean,),
            )
            row = cursor.fetchone()
            if not row or not row["password_hash"]:
                raise ValueError("Invalid email or password.")

            if not verify_password(password, row["password_hash"]):
                raise ValueError("Invalid email or password.")

            user = UserProfile(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                avatar_url=row["avatar_url"],
                provider=row["provider"],
                created_at=row["created_at"],
            )
            token = self.create_access_token(user.id, user.email)
            return user, token

    def oauth_login(
        self,
        provider: str,
        email: str,
        name: str | None = None,
        avatar_url: str | None = None,
    ) -> tuple[UserProfile, str]:
        email_clean = email.strip().lower()
        provider_clean = provider.strip().lower()

        default_name = name or (email_clean.split("@")[0].title() if "@" in email_clean else "Learner")
        default_avatar = avatar_url or f"https://api.dicebear.com/7.x/identicon/svg?seed={email_clean}"

        with _get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, name, avatar_url, provider, created_at FROM users WHERE email = ?",
                (email_clean,),
            )
            row = cursor.fetchone()
            now = time.time()

            if row:
                user_id = row["id"]
                # Update provider if needed
                cursor.execute(
                    "UPDATE users SET provider = ?, avatar_url = COALESCE(avatar_url, ?) WHERE id = ?",
                    (provider_clean, default_avatar, user_id),
                )
                conn.commit()
                user = UserProfile(
                    id=user_id,
                    name=row["name"],
                    email=row["email"],
                    avatar_url=row["avatar_url"] or default_avatar,
                    provider=provider_clean,
                    created_at=row["created_at"],
                )
            else:
                user_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO users (id, email, name, password_hash, avatar_url, provider, created_at)
                    VALUES (?, ?, ?, NULL, ?, ?, ?)
                    """,
                    (user_id, email_clean, default_name, default_avatar, provider_clean, now),
                )
                conn.commit()
                user = UserProfile(
                    id=user_id,
                    name=default_name,
                    email=email_clean,
                    avatar_url=default_avatar,
                    provider=provider_clean,
                    created_at=now,
                )

        token = self.create_access_token(user.id, user.email)
        return user, token

    def get_user_by_id(self, user_id: str) -> UserProfile | None:
        with _get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, name, avatar_url, provider, created_at FROM users WHERE id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return UserProfile(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                avatar_url=row["avatar_url"],
                provider=row["provider"],
                created_at=row["created_at"],
            )


auth_service = AuthService()
