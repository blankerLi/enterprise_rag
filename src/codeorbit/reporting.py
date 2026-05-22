from __future__ import annotations

from .models import Run


def render_markdown_report(run: Run) -> str:
    lines = [
        f"# MiMo CodeOrbit Run #{run.id}",
        "",
        f"- Repository: `{run.repo_path}`",
        f"- Task: {run.task}",
        f"- Status: `{run.status}`",
        f"- Model: `{run.model}`",
        "",
    ]
    if run.error:
        lines += ["## Error", "", run.error, ""]
    if run.snapshot:
        lines += [
            "## Repository Snapshot",
            "",
            f"- Languages: {', '.join(f'{k} ({v})' for k, v in run.snapshot.languages.items()) or 'None detected'}",
            f"- Key files: {', '.join(run.snapshot.key_files) or 'None detected'}",
            f"- Dependency files: {', '.join(run.snapshot.dependency_files) or 'None detected'}",
            f"- Test commands: {', '.join(run.snapshot.test_commands) or 'None detected'}",
            "",
        ]
    if run.result:
        result = run.result
        lines += [
            "## Clarification",
            "",
            result.clarification,
            "",
            "## Relevant Files",
            "",
            *[f"- `{path}`" for path in result.relevant_files],
            "",
            "## Implementation Plan",
            "",
            *[f"{index}. {step}" for index, step in enumerate(result.implementation_plan, start=1)],
            "",
            "## Risks",
            "",
            *[f"- {risk}" for risk in result.risks],
            "",
            "## Suggested Diff",
            "",
            "```diff",
            result.suggested_diff,
            "```",
            "",
            "## Test Plan",
            "",
            *[f"- {item}" for item in result.test_plan],
            "",
            "## Xiaomi MiMo Orbit Application Copy",
            "",
            result.application_copy,
            "",
        ]
    return "\n".join(lines)
