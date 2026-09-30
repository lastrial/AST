# AI Software Team

面向 Codex 的软件工程技能：根据任务风险选择 Lean、Balanced 或 Assurance 流程，并分别为子代理选择模型和推理强度。

## 当前版本

2026-09-30 版新增 `gpt-6.1-sol`、`gpt-6-sol` 和 `gpt-6-luna`，保留旧模型及 schema v3。实际可用组合以当前子代理启动工具为准。

- [技能入口](ai-software-team/SKILL.md)
- [安装、升级与回滚](ai-software-team/README.md)
- [模型路由规则](ai-software-team/references/model-routing.md)
- [下载移植包](ai-software-team-portable-20260930.zip) · [SHA-256](ai-software-team-portable-20260930.zip.sha256)

## 验证

```sh
python3 -B -m unittest discover -s ai-software-team/scripts -p 'test_validate_team_plan.py'
```

本次升级通过 57 项回归测试、独立 QA 与评审，以及解压后的移植验证。新模型用例采用模拟启动工具证据；真实可用性和效果仍需在目标运行环境确认。
