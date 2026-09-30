# AI Software Team：安装与移植说明

发布日期：2026-09-30。此包新增 GPT-6.1 Sol、GPT-6 Sol 和 GPT-6 Luna 的模型路由与校验，保留旧模型，团队计划格式仍为 **schema v3**。

将压缩包复制到另一台电脑，解压后安装整个 `ai-software-team` 文件夹即可。包内是实际文件，内部引用使用相对路径，不依赖原电脑的用户名、项目位置或符号链接。

## 1. 包内内容

```text
ai-software-team/
├── README.md                         本安装说明、升级摘要与验证方法
├── SKILL.md                          技能入口与编排规则
├── agents/
│   └── openai.yaml                   技能名称、默认提示词及隐式调用设置
├── references/
│   ├── model-routing.md             主代理、子代理及推理强度选用规则
│   ├── task-routing.md              任务分级与 Lean/Balanced/Assurance 路由
│   ├── execution-protocol.md         v3 计划、委派、执行预算与运行回执
│   ├── role-catalog.md               角色职责、触发条件与独立性约束
│   └── evaluation-cases.md           行为评估场景与实际调用数据统计方法
└── scripts/
    ├── validate_team_plan.py         团队计划与运行回执校验器
    └── test_validate_team_plan.py    校验器回归测试
```

完整工作规则以 [SKILL.md](SKILL.md) 及其引用为准。本说明供安装和维护使用。

## 2. 目标电脑需要什么

- 能加载本地技能的 Codex 环境。实际多代理执行还需要该环境提供子代理启动能力；子代理模型和推理强度以目标环境当时公布的可用组合为准。
- **Python 3**：用于执行计划校验与测试；本版已在 Python 3.9.6 上验证。两个脚本只使用 Python 标准库，无需 `pip install`、Node.js 或额外 API 密钥。
- 登录、模型权限、工具权限与项目开发依赖由目标环境提供。这个包不包含账号凭据、全局 `config.toml`、个人或项目 `AGENTS.md`、对话历史，也不会修改默认模型。
- `technical-direction-review` 是可配合使用的独立技能，未包含在此包内。AST 保留自身的方向门禁；若需要复现另一台电脑上的完整 TDR 工作流，应单独安装该技能。若目标任务明确要求该技能而尚未安装，应说明缺失，不能声称已执行它。

## 3. 安装位置

新安装优先使用用户级目录，使其可供多个项目使用：

| 运行环境 | 完整安装目录 |
| --- | --- |
| macOS / Linux | `~/.agents/skills/ai-software-team/` |
| Windows 原生 Codex | `%USERPROFILE%\.agents\skills\ai-software-team\` |
| 仅限当前项目 | `<项目根目录>/.agents/skills/ai-software-team/` |

用户级与项目级目录来自 [Codex 官方技能文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)，核对日期为 2026-09-05。Windows 路径是用户主目录写法的对应形式；若 Codex 实际运行在 WSL、远程主机或容器中，请安装到那个运行环境内的用户目录。

若目标电脑现有安装使用 `~/.codex/skills` 或配置过其他技能目录，先确认它确实被该环境发现，再更新那一份。不要在多个扫描目录中保留同名副本；同名技能不会自动合并。[官方说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

### 最短安装步骤

1. 将 `ai-software-team-portable-20260930.zip` 复制到目标电脑并解压。
2. 如果已有旧版，先按下文“升级与回滚”移出备份。
3. 将解压得到的整个 `ai-software-team` 文件夹复制到选定的 `skills` 目录下。
4. 检查入口路径恰好是 `skills/ai-software-team/SKILL.md`，避免多套一层文件夹。
5. Codex 通常自动发现技能变化；若未出现，重启 Codex 后再试。[官方说明](https://learn.chatgpt.com/docs/build-skills#create-a-skill)

以下命令是手动复制的替代方法。请先在终端进入**包含解压后 `ai-software-team` 文件夹的目录**。命令遇到已有安装时会停止，避免把新旧文件混在一起。

### macOS / Linux

```sh
(
  set -eu
  ast_source="$PWD/ai-software-team"
  ast_target="$HOME/.agents/skills/ai-software-team"
  test -f "$ast_source/SKILL.md"
  if [ -e "$ast_target" ] || [ -L "$ast_target" ]; then
    printf '%s\n' '已有安装，请先按“升级与回滚”备份并移出旧目录。'
    exit 1
  fi
  mkdir -p "$(dirname "$ast_target")"
  cp -R "$ast_source" "$ast_target"
)
```

### Windows PowerShell

```powershell
$astSource = Join-Path (Get-Location).Path "ai-software-team"
$astTarget = Join-Path $env:USERPROFILE ".agents\skills\ai-software-team"
if (-not (Test-Path -LiteralPath (Join-Path $astSource "SKILL.md") -PathType Leaf)) {
    throw "请进入包含解压后 ai-software-team 文件夹的目录。"
}
if (Test-Path -LiteralPath $astTarget) {
    throw "已有安装，请先按“升级与回滚”备份并移出旧目录。"
}
New-Item -ItemType Directory -Path (Split-Path -Parent $astTarget) -Force -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath $astSource -Destination $astTarget -Recurse -ErrorAction Stop
```

## 4. 安装后验证与使用

在**已安装的 `ai-software-team` 文件夹内**运行：

```sh
python3 -B -m unittest discover -s scripts -p 'test_validate_team_plan.py'
```

Windows 若使用 Python Launcher，则运行：

```powershell
py -3 -B -m unittest discover -s scripts -p "test_validate_team_plan.py"
```

确认测试全部通过并显示 `OK`。若你的 Python 命令是 `python`，将上面的解释器名称替换为对应命令。测试通过证明包内规则校验器可运行，不代表目标电脑已获得任何特定模型或多代理权限。

随后在 Codex 输入一条真实软件任务，例如：

```text
$ai-software-team 修复当前项目中的这个缺陷：<症状和复现步骤>。
先检查仓库证据，选择合适的执行模式，并按当前可用模型和任务需要分配工作。
```

局部、低风险的任务可以由主代理独立完成；技能没有要求每次都创建团队。显式调用与按任务匹配自动调用均受支持，包内 `agents/openai.yaml` 已开启隐式调用。

让代理生成完整 v3 团队计划后，可在技能目录运行：

```sh
python3 -B scripts/validate_team_plan.py /path/to/team-plan.json
python3 -B scripts/validate_team_plan.py /path/to/team-plan.json --receipt /path/to/runtime-receipt.json
```

把示例文件路径替换为实际路径；Windows 同样可用 `py -3` 替换 `python3`。退出码 `0` 表示校验通过，`1` 表示规则校验失败，`2` 表示文件、JSON 读取或命令参数错误。[执行协议](references/execution-protocol.md)中的 JSON 是局部示例，不能直接当完整计划运行。测试夹具中的模型矩阵也不能充当目标环境的真实可用性证据。

## 5. 本版模型规则摘要

完整选用规则见 [model-routing.md](references/model-routing.md)。以下是本技能策略，组合是否可调用仍由当前运行环境决定。

| 项目 | 本版规则 |
| --- | --- |
| 主代理起点 | 尊重用户当前模型与推理强度，不强制 Sol/high；当前任务证据无法确认的字段保留为未知 |
| 主代理调整 | 按复杂度、风险、不确定性与已发现的能力缺口选择 `stay`、`delegate-up` 或建议 `switch-root`；用户保留最终选择 |
| Luna 子代理 | 两代 Luna 均仅限已有 Balanced 团队中的全低风险、只读事实收集；新模型的通用编码能力不会自动扩大本技能允许的职责 |
| Terra 子代理 | 普通实现、测试、诊断与审查；包括有充分依据的 Terra/low 等组合 |
| Sol / Astra 子代理 | 新 Sol 可承担普通工程和关键判断；Astra 用于有具体依据的更困难分析或工程工作；保留旧 Sol 路由 |
| 推理强度 | 模型与强度分别选择；计划词汇为 `low`、`medium`、`high`、`xhigh`、`max`、`ultra`，每个实际组合必须由当前子代理启动工具确认；不同代的同名档位不等价 |
| Ultra | GPT-6 Luna 不支持；其他模型也需确认启动工具行为能够遵守子代理不得再次委派的边界，否则选足够的非 Ultra 档位 |
| 关键职责下限 | Security Reviewer、Devil’s Advocate 及 Assurance 关键判断使用 Sol 或 Astra 的 high 及以上组合 |
| 起始档位 | 新 Luna 可从 high、旧 Luna 可从 low 起步；具体任务证据可支持调整，起始建议不是调用配额或性能保证 |
| 调用比例 | 不预设命中率，不承诺模型间效果等价；实际频率、适用性与成本应分别依据真实任务数据统计 |

注册模型 ID 为 `gpt-6.1-sol`、`gpt-6-sol`、`gpt-6-luna`、`gpt-6-astra`、`gpt-5.6-sol`、`gpt-5.6-terra` 和 `gpt-5.6-luna`。同一系列内可优先考虑已确认可用的新代模型；用户选择和可比任务的验证结果可以支持其他组合。

注册表表示技能认识这些模型，`runtime.available_models` 才表示当前子代理启动工具确认可用的组合。主对话选择器、创建聊天的工具和官方文档不能替代子代理可用性证据；迁移技能不会开通模型。新 Sol/Luna 未开放时，继续使用满足要求的旧模型或 Astra。关键任务只有在所有已注册 Sol 代际和 Astra 都没有可用 high 及以上组合时，才能按规则声明缺少关键模型能力。

Sol 共用 `sol_`、Luna 共用 `luna_` 任务名前缀，但计划和运行回执仍须使用并匹配完整模型 ID。不能把 `gpt-6-sol` 的执行记作 `gpt-6.1-sol`。

## 6. 升级与回滚

1. 找到目标环境实际加载的旧版目录，并结束正在使用它的任务。
2. 将旧版完整复制到**技能扫描目录之外**，例如用户目录下的 `codex-skill-backups/ai-software-team-旧日期/`。不要只在 `skills` 里改名留作备份，否则仍可能被发现。
3. 若旧安装是符号链接，先复制其指向的实际文件作为备份，再移出安装链接；不要误删链接指向的开发项目。新包可以直接以普通目录安装。
4. 将旧安装移出加载位置，再按安装步骤复制新版完整目录并运行测试。
5. 需要回滚时，将新版移出加载位置，恢复备份到原安装路径，再让 Codex 重新加载。

本次升级保留 schema v3、旧模型 ID、职责边界及既有有效计划，不新增必填字段。新 Luna 的 `ultra` 会在可用性列表和路由中被拒绝。`critical-high-plus` 表示所有已注册 Sol 代际与 Astra 均无可用 high+ 组合；旧名 `sol-high-plus` 仅作为相同含义的兼容别名，任何新 Sol/high+ 可用时也不能据此豁免。重新执行旧计划时，仍需刷新运行环境证据并校验。

## 7. 包完整性与常见问题

压缩包旁提供同名 `.zip.sha256` 文件。传输时可一并复制，用它检查 ZIP 是否完整：

```sh
# macOS，在 ZIP 和校验文件所在目录运行
shasum -a 256 -c ai-software-team-portable-20260930.zip.sha256
```

Linux 可将上面的 `shasum -a 256` 替换为 `sha256sum`。Windows PowerShell 可运行以下命令，把 `Hash` 与校验文件中的值比较：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\ai-software-team-portable-20260930.zip
Get-Content -LiteralPath .\ai-software-team-portable-20260930.zip.sha256
```

- **看不到技能**：检查完整入口路径、实际运行主机、同名副本及现有禁用配置；然后重启 Codex。不要为了安装技能覆盖整个全局配置。
- **无法创建子代理或模型不可用**：检查目标 Codex 环境提供的工具和模型权限。校验器不会替你启动代理，也不会开通模型。
- **无法确认主代理模型或强度**：保留相应字段为未知；不能从默认配置、模型列表或另一条任务推断当前组合，也不因此阻止普通工作。
- **解压后运行测试失败**：确认复制了整个目录、在技能目录执行命令，并且使用 Python 3；保留具体报错定位问题。

发布前验证包括：在独立的中文及含空格路径下运行全部回归测试，核对归档内容与源文件一致，并检查技能结构及本地文档链接。新模型测试使用模拟启动工具证据，不能据此声称已完成新模型的真实调用或效果评测。Windows PowerShell 安装命令已提供，尚未在 Windows 主机实测。
