"""QuizSession – pure state container, no Telegram dependency."""
from __future__ import annotations

import asyncio
import random


class QuizSession:
    def __init__(
        self,
        user_id: int,
        chat_id: int,
        questions: list[dict],
        shuffle: bool = False,
    ) -> None:
        self.user_id = user_id
        self.chat_id = chat_id
        self.questions = questions[:]
        if shuffle:
            random.shuffle(self.questions)

        self.total          = len(self.questions)
        self.current_index  = 0
        self.score          = 0
        self.active         = True

        # incremented before each question; lets the callback detect stale taps
        self.question_id    = 0
        self.awaiting_answer = False
        self.current_msg_id: int | None          = None
        self.timer_task:     asyncio.Task | None = None

        # {category: {total: int, correct: int}}
        self.cat_scores: dict[str, dict] = {}

    # ── properties ────────────────────────────────────────────────────────────

    @property
    def current_question(self) -> dict | None:
        if self.current_index < self.total:
            return self.questions[self.current_index]
        return None

    # ── mutations ─────────────────────────────────────────────────────────────

    def record(self, category: str, is_correct: bool) -> None:
        cs = self.cat_scores.setdefault(category, {"total": 0, "correct": 0})
        cs["total"] += 1
        if is_correct:
            cs["correct"] += 1
            self.score += 1

    def advance(self) -> None:
        self.current_index += 1

    def stop(self) -> None:
        self.active = False
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
