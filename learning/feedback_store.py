import json
import sqlite3
from datetime import datetime

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    rating INTEGER NOT NULL,
    issue_summary TEXT DEFAULT '',
    resolved INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS learning_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposed_heuristic TEXT NOT NULL,
    source_session_ids TEXT DEFAULT '[]',
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now')),
    reviewed_at TEXT
);
"""


class FeedbackStore:
    def __init__(self, db_path: str = "./learning/feedback.db"):
        self._db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._conn()
        try:
            conn.executescript(_CREATE_TABLES)
        finally:
            conn.close()

    def close(self) -> None:
        """No-op public API: all connections are closed after each operation."""
        pass

    def record(self, session_id: str, user_id: str, rating: int,
               issue_summary: str = "", resolved: bool = False) -> None:
        conn = self._conn()
        try:
            conn.execute(
                "INSERT INTO feedback (session_id, user_id, rating, issue_summary, resolved) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, user_id, rating, issue_summary, int(resolved)),
            )
            conn.commit()
        finally:
            conn.close()

    def get_all(self) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM feedback ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_negative_feedback(self) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM feedback WHERE rating = -1 ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_proposal(self, heuristic: str, session_ids: list[str]) -> int:
        conn = self._conn()
        try:
            cur = conn.execute(
                "INSERT INTO learning_proposals (proposed_heuristic, source_session_ids) "
                "VALUES (?, ?)",
                (heuristic, json.dumps(session_ids)),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_pending_proposals(self) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM learning_proposals WHERE status = 'pending' ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_proposal_status(self, proposal_id: int, status: str) -> None:
        conn = self._conn()
        try:
            conn.execute(
                "UPDATE learning_proposals SET status = ?, reviewed_at = datetime('now') "
                "WHERE id = ?",
                (status, proposal_id),
            )
            conn.commit()
        finally:
            conn.close()
