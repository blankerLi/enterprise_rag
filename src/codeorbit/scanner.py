from __future__ import annotations

import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from .models import FileSnippet, RepoSnapshot


IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".cache",
    "target",
}

LANG_BY_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".md": "Markdown",
    ".json": "JSON",
    ".toml": "TOML",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".html": "HTML",
    ".css": "CSS",
}

DEPENDENCY_FILES = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "composer.json",
}

README_NAMES = {"readme.md", "readme.txt", "readme"}


def scan_repository(repo_path: str, task: str | None = None, max_snippets: int = 18) -> RepoSnapshot:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {root}")

    languages: Counter[str] = Counter()
    key_files: list[str] = []
    dependency_files: list[str] = []
    candidates: list[tuple[int, Path]] = []
    terms = _task_terms(task or "")

    for file_path in _iter_files(root):
        rel = file_path.relative_to(root).as_posix()
        language = LANG_BY_SUFFIX.get(file_path.suffix.lower())
        if language:
            languages[language] += 1
        lower_name = file_path.name.lower()
        if lower_name in README_NAMES or lower_name in DEPENDENCY_FILES:
            key_files.append(rel)
        if lower_name in DEPENDENCY_FILES:
            dependency_files.append(rel)
        if _is_text_like(file_path):
            score = _score_file(file_path, rel, terms)
            if score > 0:
                candidates.append((score, file_path))

    snippets = [
        _read_snippet(root, path, score)
        for score, path in sorted(candidates, key=lambda item: item[0], reverse=True)[:max_snippets]
    ]

    return RepoSnapshot(
        root=str(root),
        generated_at=datetime.now(UTC),
        languages=dict(languages.most_common()),
        key_files=sorted(set(key_files))[:40],
        dependency_files=sorted(set(dependency_files)),
        test_commands=_infer_test_commands(root),
        snippets=snippets,
    )


def _iter_files(root: Path):
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORE_DIRS]
        for file_name in files:
            path = Path(current_root) / file_name
            if path.stat().st_size <= 256_000:
                yield path


def _task_terms(task: str) -> set[str]:
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in task)
    return {term for term in normalized.split() if len(term) >= 2}


def _is_text_like(path: Path) -> bool:
    if path.suffix.lower() in LANG_BY_SUFFIX:
        return True
    return path.name.lower() in DEPENDENCY_FILES or path.name.lower() in README_NAMES


def _score_file(path: Path, rel: str, terms: set[str]) -> int:
    score = 1
    lower_rel = rel.lower()
    if path.name.lower() in README_NAMES:
        score += 12
    if path.name.lower() in DEPENDENCY_FILES:
        score += 10
    if any(part in lower_rel for part in ["test", "spec", "src", "app", "api", "service"]):
        score += 4
    if terms:
        score += sum(5 for term in terms if term in lower_rel)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()[:40_000]
            score += sum(3 for term in terms if term in text)
        except OSError:
            pass
    return score


def _read_snippet(root: Path, path: Path, score: int) -> FileSnippet:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = path.relative_to(root).as_posix()
    return FileSnippet(
        path=rel,
        language=LANG_BY_SUFFIX.get(path.suffix.lower(), "Text"),
        score=score,
        content=text[:12_000],
    )


def _infer_test_commands(root: Path) -> list[str]:
    commands: list[str] = []
    names = {path.name.lower() for path in root.iterdir() if path.is_file()}
    if "pyproject.toml" in names or "pytest.ini" in names or "requirements.txt" in names:
        commands.append("pytest")
    if "package.json" in names:
        commands.extend(["npm test", "npm run lint"])
    if "go.mod" in names:
        commands.append("go test ./...")
    if "cargo.toml" in names:
        commands.append("cargo test")
    return commands or ["No test command detected; inspect project docs."]
