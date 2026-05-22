# MiMo CodeOrbit Run #1

- Repository: `examples/demo-repo`
- Task: 帮我给登录失败增加重试限制
- Status: `completed`
- Model: `mimo-coding`

## Repository Snapshot

- Languages: Python (2), TOML (1), Markdown (1)
- Key files: README.md, pyproject.toml
- Dependency files: pyproject.toml
- Test commands: pytest

## Clarification

目标是围绕真实仓库完成需求：帮我给登录失败增加重试限制。

## Relevant Files

- `auth_service.py`
- `tests/test_auth_service.py`
- `README.md`
- `pyproject.toml`

## Implementation Plan

1. 确认登录失败重试限制的业务规则，包括按用户名、IP 还是会话维度计数。
2. 在 `AuthService` 中加入失败次数记录和锁定判断，保持现有 `login` 接口简单可测。
3. 为成功登录重置失败次数、连续失败触发限制、未知用户失败场景补充测试。
4. 将实现计划、候选 diff、风险和测试方案整理为小米 MiMo Orbit 申请证明材料。

## Risks

- 当前报告来自离线演示模式，未调用真实 MiMo 模型。
- 失败次数存储在内存中，仅适合 MVP；生产环境需要持久化或缓存层。
- 重试限制可能影响正常用户，需要定义锁定窗口和提示策略。

## Suggested Diff

```diff
diff --git a/auth_service.py b/auth_service.py
--- a/auth_service.py
+++ b/auth_service.py
@@ -2,9 +2,18 @@
 class AuthService:
-    def __init__(self, users: dict[str, str]) -> None:
+    def __init__(self, users: dict[str, str], max_failures: int = 3) -> None:
         self.users = users
+        self.max_failures = max_failures
+        self.failures: dict[str, int] = {}
 
     def login(self, username: str, password: str) -> bool:
+        if self.failures.get(username, 0) >= self.max_failures:
+            return False
         expected = self.users.get(username)
-        return expected == password
+        if expected == password:
+            self.failures[username] = 0
+            return True
+        self.failures[username] = self.failures.get(username, 0) + 1
+        return False
```

## Test Plan

- `pytest`
- 测试同一用户连续失败 3 次后被拒绝。
- 测试成功登录后失败次数清零。
- 测试未知用户失败不会绕过限制。

## Xiaomi MiMo Orbit Application Copy

MiMo CodeOrbit 是一个基于小米 MiMo 的仓库级 AI 编程助手，可分析真实 Python、JavaScript 或多语言项目，自动生成需求澄清、相关文件定位、实现计划、风险评估、候选 diff 和测试方案。项目强调长上下文代码理解、多轮 Agent 工作流和真实开发效率提升，适合持续消耗 Token 的开发者场景，可作为 MiMo Orbit 百万亿 Token 创造者激励计划的高频应用案例。
