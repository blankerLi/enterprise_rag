from pathlib import Path

from codeorbit.scanner import scan_repository


def test_scan_empty_repository(tmp_path: Path) -> None:
    snapshot = scan_repository(str(tmp_path), task="测试")
    assert snapshot.root == str(tmp_path)
    assert snapshot.languages == {}
    assert snapshot.test_commands


def test_scan_python_repository(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("def login():\n    return True\n", encoding="utf-8")
    snapshot = scan_repository(str(tmp_path), task="登录失败重试限制")
    assert snapshot.languages["Python"] == 1
    assert "README.md" in snapshot.key_files
    assert "pyproject.toml" in snapshot.dependency_files
    assert "pytest" in snapshot.test_commands
