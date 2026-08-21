"""
Lightweight SQLite-backed storage for chat sessions and messages.

Phase 1 doesn't need a distributed store (see the project's architecture
report — the same "small, static, single-team" reasoning applies here): a
single file-based database keeps chat history across server restarts
without adding any infrastructure.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL DEFAULT 'New chat',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    citations   TEXT,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        columns = [row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()]
        if "citations" not in columns:
            conn.execute("ALTER TABLE messages ADD COLUMN citations TEXT")


@contextmanager
def get_conn():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_session(title: str = "New chat") -> dict:
    session_id = str(uuid.uuid4())
    now = _now()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, title, now, now),
        )
    return {"id": session_id, "title": title, "created_at": now, "updated_at": now}


def list_sessions() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_session(session_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return dict(row) if row else None


def ensure_session(session_id: str) -> None:
    if get_session(session_id) is None:
        now = _now()
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, "New chat", now, now),
            )


def rename_session_if_default(session_id: str, first_user_message: str) -> None:
    """Auto-title a session from its first user message, once."""
    title = first_user_message.strip().replace("\n", " ")
    if len(title) > 48:
        title = title[:45].rstrip() + "..."
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET title = ? WHERE id = ? AND title = 'New chat'",
            (title or "New chat", session_id),
        )


def touch_session(session_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?", (_now(), session_id)
        )


def delete_session(session_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


def add_message(session_id: str, role: str, content: str, citations: list[dict] | None = None) -> dict:
    now = _now()
    citations_json = json.dumps(citations) if citations else None
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO messages (session_id, role, content, citations, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, citations_json, now),
        )
        msg_id = cur.lastrowid
    return {
        "id": msg_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "citations": citations,
        "created_at": now,
    }


def get_messages(session_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, role, content, citations, created_at FROM messages "
            "WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()

    result = []
    for r in rows:
        d = dict(r)
        c_str = d.pop("citations", None)
        if c_str:
            try:
                d["citations"] = json.loads(c_str)
            except Exception:
                d["citations"] = []
        else:
            d["citations"] = []
        result.append(d)
    return result
