from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


RunStatus = Literal["pending", "running", "completed", "failed"]


class FileSnippet(BaseModel):
    path: str
    language: str
    score: int
    content: str


class RepoSnapshot(BaseModel):
    root: str
    generated_at: datetime
    languages: dict[str, int] = Field(default_factory=dict)
    key_files: list[str] = Field(default_factory=list)
    dependency_files: list[str] = Field(default_factory=list)
    test_commands: list[str] = Field(default_factory=list)
    snippets: list[FileSnippet] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    clarification: str
    relevant_files: list[str] = Field(default_factory=list)
    implementation_plan: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggested_diff: str = ""
    test_plan: list[str] = Field(default_factory=list)
    application_copy: str = ""


class Run(BaseModel):
    id: int | None = None
    repo_path: str
    task: str
    status: RunStatus = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model: str = ""
    error: str | None = None
    snapshot: RepoSnapshot | None = None
    result: AnalysisResult | None = None
