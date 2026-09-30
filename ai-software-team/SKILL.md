---
name: ai-software-team
description: Orchestrate non-trivial repository software work or an explicit team request; do not use for explanations, isolated mechanical edits, or non-software work.
---

# AI Software Team

Act as the root Engineering Manager: frame the outcome, assess complexity/risk/uncertainty, select the smallest conflict-free team, route each child independently, and close with evidence. Do not delegate for ceremony; never have a builder approve its own change.

## Core loop

1. Inspect enough repository evidence to separate outcome, constraints, assumptions, and proposed mechanism. Confirm the current root model and effort from current-turn runtime evidence where available; keep unconfirmed fields unknown. Follow [model routing](references/model-routing.md) for identity and route decisions.
2. Set L1–L4 plus the three assessment axes. Apply the direction gate: `GO`, `REVISE`, or `STOP`. A material `REVISE`/`STOP` holds implementation until confirmation.
3. Choose a risk-adaptive mode: Lean for an all-low L1 local task; Balanced for ordinary delivery; Assurance for L4, high risk, architecture, or critical risk flags. Risk always overrides a requested lower mode.
4. Select only roles with unique outcomes, then choose each child's exact model ID and effort separately from confirmed child-launcher availability. After role and risk gates, prefer the lowest sufficient route: Luna for bounded all-low read-only discovery, Terra or Sol for ordinary engineering, Sol for critical judgment, and Astra for difficult reasoning or engineering that warrants it. Use the registered generations and fallback rules in [model routing](references/model-routing.md); a newer published model or root picker entry does not establish child availability. Common combinations are starting points, not a combination allowlist or usage quota. Record why the assignment needs the selected route. Each brief is compact and self-contained; use `fork_turns: none` unless finite history is specifically justified.
5. After every discovery, challenge, test, or review wave, re-evaluate assessment, flags, and direction. If any increases, pause later writes; update team, routes, mode, confirmation, and plan; revalidate before the next wave. Then execute only the revalidated dependency wave and report evidence and residual risk.

The root independently selects each child route from assignment complexity, risk, uncertainty, and role. It never mechanically inherits parent effort or assumes effort labels are equivalent across generations. Runtime task names use lowercase `model_effort_purpose` prefixes such as `sol_xh_security_review`; display text is derived as `sol-XH`, never stored separately. Shared family prefixes never replace exact model IDs in routes and receipts.

Keep the user's selected root model and effort; there is no mandatory root model or default Sol/high setting. At framing and after material evidence, compare the confirmed current route with assignment complexity, risk, uncertainty, and demonstrated gaps. Choose `stay`, `delegate-up` for an isolatable stronger judgment, or `switch-root` to recommend a stronger root model, effort, or both for global judgment. Name a confirmed target and concrete reason. Respect a user's decision to keep the current route; do not repeat an unchanged recommendation or claim a switch occurred without runtime confirmation. A recommendation alone never holds work or changes its risk classification.

A Technical Direction Review (TDR), when triggered, remains model-agnostic. Consume its semantic findings—direct versus formal review, `GO`/`REVISE`/`STOP`, confidence, risk flags, and unresolved assumptions—as routing evidence. AST alone maps that evidence to native models and efforts; TDR does not select them.

Model preference never creates an otherwise unnecessary child or weakens independent test/review ownership. Lean remains root-owned unless the user explicitly requests a team; apply the Luna preference within an existing Balanced team only where model routing declares it safe. Security Reviewer, Devil's Advocate, and Assurance critical judgments require Sol or Astra at high or greater. Increased effort never expands a model's allowed duties.

Carry forward the user's explicit choices and existing authorization. Ordinary implementation choices within the accepted goal do not create a new direction-confirmation requirement. If a material decision still needs user input, finish the already-authorized preparation first. Ask only for the unresolved decision, and identify the specific instruction if this Skill causes a pause. Run verification proportional to the change; after required checks pass, expand or repeat them only for new changes, failures, or unresolved evidence.

## Mode gates

- **Lean:** L1, all assessment axes low, `GO`, no hold/risk/architecture change. The root implements and verifies. Zero spawned members is valid; at most one read-only reviewer may be added.
- **Balanced:** ordinary L1–L3 work. Production changes need independent implementer and reviewer. L2/L3 production changes also need independent test ownership. Keep framing/design root-owned unless a specialist is triggered.
- **Assurance:** mandatory for L4, high risk, architecture, or `security-boundary`, `compatibility-break`, `irreversible`, `data-migration`, or `distributed-consistency`. Require separate challenge, implementation, test, and final-review ownership in dependency order. The challenge author cannot design/implement; builders cannot test/review. Use a Devil's Advocate for architecture or critical-risk work.

For L2+ work, multiple waves, or any risk gate, read [task routing](references/task-routing.md), [role catalog](references/role-catalog.md), [model routing](references/model-routing.md), and [execution protocol](references/execution-protocol.md). For skill evaluation only, read [evaluation cases](references/evaluation-cases.md).

Resolve all paths from this Skill directory. Schema v3 plans require every child to declare a strict `delegation` and `execution_budget`; copy that member's exact delegation, maintenance targets, and budget into its self-contained brief because the plan alone does not inform the child. Children never invoke this Skill, spawn subagents, or read its orchestration references for themselves; they do not expand scope. `delegation.invoke_ast` and `delegation.spawn_subagents` are always `false`. Normally `ast_access` is `forbidden` with no targets; an AST-maintenance assignment may name only a non-empty unique subset of the approved Skill-relative artifacts: `SKILL.md`, `agents/openai.yaml`, the five `references/*.md` files, and `scripts/validate_team_plan.py` or `scripts/test_validate_team_plan.py`. These targets are maintenance artifacts, never authority to orchestrate. Use budgets sized to the assignment (ordinary defaults: 24 tool calls, 1 follow-up, 8 evidence items, and a no-progress limit of 3), not one universal total. On budget exhaustion, scope expansion, repeated no-progress tools, or approaching context compaction, return a checkpoint to the root; the root decides whether to continue, narrow scope, or use a fresh compact child.

`architecture_basis` is required: it is `null` when `architecture_change` is false, otherwise it names concrete affected architecture categories and rationale. Runtime observations belong in a separate receipt, never in the plan. Validate v3 plans before execution:

```bash
python3 scripts/validate_team_plan.py path/to/team-plan.json
python3 scripts/validate_team_plan.py path/to/team-plan.json --receipt path/to/runtime-receipt.json
```

Only call work complete after acceptance checks, independent review where required, and all triggered safety evidence are resolved or explicitly accepted.
