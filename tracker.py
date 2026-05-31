"""Persist per-user, per-category quiz scores in SQLite."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "quizbot.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                user_id  INTEGER NOT NULL,
                category TEXT    NOT NULL,
                total    INTEGER NOT NULL DEFAULT 0,
                correct  INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, category)
            )
        """)


def record_answer(user_id: int, category: str, is_correct: bool) -> None:
    inc = 1 if is_correct else 0
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            INSERT INTO scores (user_id, category, total, correct)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(user_id, category) DO UPDATE
                SET total   = total + 1,
                    correct = correct + excluded.correct
        """, (user_id, category, inc))


def get_stats(user_id: int) -> list[dict]:
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            "SELECT category, total, correct FROM scores "
            "WHERE user_id = ? ORDER BY category",
            (user_id,),
        ).fetchall()
    return [{"category": r[0], "total": r[1], "correct": r[2]} for r in rows]


def get_weak_categories(user_id: int, threshold: float = 0.70) -> list[str]:
    return [
        s["category"]
        for s in get_stats(user_id)
        if s["total"] > 0 and s["correct"] / s["total"] < threshold
    ]
