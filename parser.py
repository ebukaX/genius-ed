"""Parse .xlsx or .csv quiz files into a list of question dicts."""
from __future__ import annotations

import csv
import openpyxl
from io import BytesIO, StringIO
from pathlib import Path

REQUIRED_COLUMNS = frozenset({
    "question", "option_a", "option_b", "option_c", "option_d",
    "correct_answer", "category",
})


def parse_file(data: bytes, filename: str) -> list[dict]:
    ext = Path(filename).suffix.lower()
    if ext in (".xlsx", ".xls"):
        return _parse_xlsx(data)
    if ext == ".csv":
        return _parse_csv(data)
    raise ValueError(
        f"Unsupported file type '{ext}'. Please send an .xlsx or .csv file."
    )


# ── internals ──────────────────────────────────────────────────────────────────

def _norm_headers(raw: list) -> list[str]:
    return [str(v).strip().lower() if v is not None else "" for v in raw]


def _validate(headers: list[str]) -> None:
    missing = REQUIRED_COLUMNS - set(headers)
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}\n"
            f"Required: {', '.join(sorted(REQUIRED_COLUMNS))}"
        )


def _to_question(mapping: dict) -> dict | None:
    question = str(mapping.get("question") or "").strip()
    if not question or question.lower() == "none":
        return None

    ans = str(mapping.get("correct_answer") or "").strip().lower()
    if ans not in ("a", "b", "c", "d"):
        return None  # skip malformed rows silently

    try:
        tl = int(str(mapping.get("time_limit") or "15").strip() or "15")
        tl = max(10, min(120, tl))
    except (ValueError, TypeError):
        tl = 15

    return {
        "question":       question,
        "option_a":       str(mapping.get("option_a") or "").strip(),
        "option_b":       str(mapping.get("option_b") or "").strip(),
        "option_c":       str(mapping.get("option_c") or "").strip(),
        "option_d":       str(mapping.get("option_d") or "").strip(),
        "correct_answer": ans,
        "category":       str(mapping.get("category") or "General").strip() or "General",
        "time_limit":     tl,
    }


def _parse_xlsx(data: bytes) -> list[dict]:
    wb = openpyxl.load_workbook(BytesIO(data))
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("The spreadsheet is empty.")

    headers = _norm_headers(rows[0])
    _validate(headers)

    questions: list[dict] = []
    for row in rows[1:]:
        mapping = {
            headers[i]: (row[i] if i < len(row) else None)
            for i in range(len(headers))
        }
        q = _to_question(mapping)
        if q:
            questions.append(q)
    return questions


def _parse_csv(data: bytes) -> list[dict]:
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV file has no header row.")

    headers = [h.strip().lower() for h in reader.fieldnames]
    _validate(headers)

    questions: list[dict] = []
    for row in reader:
        mapping = {k.strip().lower(): v for k, v in row.items()}
        q = _to_question(mapping)
        if q:
            questions.append(q)
    return questions
