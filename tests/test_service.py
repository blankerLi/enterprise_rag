from pathlib import Path

from codeorbit.llm import LLMClient
from codeorbit.service import CodeOrbitService
from codeorbit.storage import RunStore


def test_demo_mode_run_completes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "package.json").write_text('{"scripts":{"test":"vitest"}}', encoding="utf-8")
    (repo / "index.js").write_text("console.log('demo')\n", encoding="utf-8")
    db_path = tmp_path / "runs.sqlite3"
    service = CodeOrbitService(RunStore(db_path), LLMClient(demo_mode=True))

    run = service.run_analysis(str(repo), "生成申请材料")

    assert run.status == "completed"
    assert run.result is not None
    assert "MiMo CodeOrbit" in run.result.application_copy
