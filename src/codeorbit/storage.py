from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .models import AnalysisResult, RepoSnapshot, Run


def default_db_path() -> Path:
    value = os.getenv("CODEORBIT_DB")
    if value:
        return Path(value).expanduser().resolve()
    return Path.cwd() / ".codeorbit" / "codeorbit.sqlite3"


class RunStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_path TEXT NOT NULL,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    model TEXT NOT NULL,
                    error TEXT,
                    snapshot_json TEXT,
                    result_json TEXT
                )
                """
            )

    def create_run(self, repo_path: str, task: str, model: str) -> Run:
        now = datetime.now(UTC)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO runs (repo_path, task, status, created_at, updated_at, model)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (repo_path, task, "pending", now.isoformat(), now.isoformat(), model),
            )
            run_id = int(cursor.lastrowid)
        return self.get_run(run_id)

    def update_run(
        self,
        run_id: int,
        *,
        status: str,
        snapshot: RepoSnapshot | None = None,
        result: AnalysisResult | None = None,
        error: str | None = None,
    ) -> Run:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE runs
                SET status = ?, updated_at = ?, snapshot_json = COALESCE(?, snapshot_json),
                    result_json = COALESCE(?, result_json), error = ?
                WHERE id = ?
                """,
                (
                    status,
                    datetime.now(UTC).isoformat(),
                    snapshot.model_dump_json() if snapshot else None,
                    result.model_dump_json() if result else None,
                    error,
                    run_id,
                ),
            )
        return self.get_run(run_id)

    def get_run(self, run_id: int) -> Run:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"Run not found: {run_id}")
        return _row_to_run(row)

    def list_runs(self) -> list[Run]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM runs ORDER BY id DESC").fetchall()
        return [_row_to_run(row) for row in rows]


def _row_to_run(row: sqlite3.Row) -> Run:
    snapshot = RepoSnapshot.model_validate(json.loads(row["snapshot_json"])) if row["snapshot_json"] else None
    result = AnalysisResult.model_validate(json.loads(row["result_json"])) if row["result_json"] else None
    return Run(
        id=row["id"],
        repo_path=row["repo_path"],
        task=row["task"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        model=row["model"],
        error=row["error"],
        snapshot=snapshot,
        result=result,
    )
