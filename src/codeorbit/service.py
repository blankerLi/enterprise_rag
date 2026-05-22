from __future__ import annotations

from .llm import LLMClient
from .models import Run
from .scanner import scan_repository
from .storage import RunStore


class CodeOrbitService:
    def __init__(self, store: RunStore | None = None, client: LLMClient | None = None) -> None:
        self.store = store or RunStore()
        self.client = client or LLMClient()

    def scan(self, repo_path: str, task: str | None = None):
        return scan_repository(repo_path, task=task)

    def run_analysis(self, repo_path: str, task: str) -> Run:
        run = self.store.create_run(repo_path=repo_path, task=task, model=self.client.model)
        try:
            self.store.update_run(run.id or 0, status="running")
            snapshot = scan_repository(repo_path, task=task)
            result = self.client.analyze(snapshot, task)
            return self.store.update_run(run.id or 0, status="completed", snapshot=snapshot, result=result)
        except Exception as exc:
            return self.store.update_run(run.id or 0, status="failed", error=str(exc))

    def list_runs(self) -> list[Run]:
        return self.store.list_runs()

    def get_run(self, run_id: int) -> Run:
        return self.store.get_run(run_id)
