from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .models import AnalysisResult, RepoSnapshot


DEFAULT_MODEL = "mimo-coding"


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        demo_mode: bool | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("MIMO_API_KEY", "")
        self.base_url = (base_url or os.getenv("MIMO_BASE_URL", "")).rstrip("/")
        self.model = model or os.getenv("MIMO_MODEL", DEFAULT_MODEL)
        self.demo_mode = demo_mode if demo_mode is not None else os.getenv("CODEORBIT_DEMO_MODE") == "1"

    def analyze(self, snapshot: RepoSnapshot, task: str) -> AnalysisResult:
        if self.demo_mode:
            return self._demo_analysis(snapshot, task)
        if not self.api_key:
            raise RuntimeError("Missing MIMO_API_KEY. Set CODEORBIT_DEMO_MODE=1 for an offline demo.")
        if not self.base_url:
            raise RuntimeError("Missing MIMO_BASE_URL. Expected an OpenAI-compatible /chat/completions endpoint.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(snapshot, task)},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"MiMo API request failed: HTTP {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"MiMo API request failed: {exc.reason}") from exc

        content = body["choices"][0]["message"]["content"]
        return self._parse_result(content)

    def _build_user_prompt(self, snapshot: RepoSnapshot, task: str) -> str:
        compact_snapshot = snapshot.model_dump(mode="json")
        return (
            "User task:\n"
            f"{task}\n\n"
            "Repository snapshot JSON:\n"
            f"{json.dumps(compact_snapshot, ensure_ascii=False)}\n\n"
            "Return JSON with keys: clarification, relevant_files, implementation_plan, "
            "risks, suggested_diff, test_plan, application_copy."
        )

    def _parse_result(self, content: str) -> AnalysisResult:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Model returned non-JSON content: {content[:500]}") from exc
        return AnalysisResult.model_validate(data)

    def _demo_analysis(self, snapshot: RepoSnapshot, task: str) -> AnalysisResult:
        files = [snippet.path for snippet in snapshot.snippets[:6]]
        language_list = ", ".join(snapshot.languages.keys()) or "unknown language"
        diff_path = files[0] if files else "src/example.py"
        return AnalysisResult(
            clarification=f"目标是围绕真实仓库完成需求：{task}",
            relevant_files=files,
            implementation_plan=[
                "确认需求影响的入口、服务层和测试层，并保留现有架构边界。",
                "在相关模块中加入最小实现，优先复用现有配置、错误处理和日志方式。",
                "补充面向成功路径、失败路径和回归风险的测试。",
                "导出 Markdown 报告和申请文案，用于 MiMo Orbit 计划材料。",
            ],
            risks=[
                "当前结果来自离线演示模式，未调用真实 MiMo 模型。",
                "建议 diff 是候选方案，应用前需要人工审查。",
                "若仓库缺少测试命令，需要先补充最小可验证场景。",
            ],
            suggested_diff=(
                f"diff --git a/{diff_path} b/{diff_path}\n"
                "index 0000000..1111111 100644\n"
                f"--- a/{diff_path}\n"
                f"+++ b/{diff_path}\n"
                "@@ -1,3 +1,8 @@\n"
                "+# MiMo CodeOrbit suggested patch placeholder\n"
                "+# Replace this block with the model-generated implementation.\n"
            ),
            test_plan=snapshot.test_commands
            + [
                "Review generated diff before applying it.",
                "Run one end-to-end smoke test for the edited workflow.",
            ],
            application_copy=(
                "MiMo CodeOrbit 是一个基于小米 MiMo 的仓库级 AI 编程助手，"
                f"可分析 {language_list} 项目，自动生成需求澄清、相关文件定位、"
                "实现计划、风险评估、候选 diff 和测试方案。项目强调长上下文代码理解、"
                "多轮 Agent 工作流和真实开发效率提升，适合持续消耗 Token 的开发者场景。"
            ),
        )


SYSTEM_PROMPT = """You are MiMo CodeOrbit, a repository-level coding agent.
Analyze the supplied repository snapshot and user task.
Return only valid JSON matching this schema:
{
  "clarification": "string",
  "relevant_files": ["path"],
  "implementation_plan": ["step"],
  "risks": ["risk"],
  "suggested_diff": "unified diff string",
  "test_plan": ["test command or scenario"],
  "application_copy": "Chinese application paragraph for Xiaomi MiMo Orbit"
}
Do not claim the diff has been applied. Keep suggestions concrete and reviewable.
"""
