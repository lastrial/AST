# Model Routing

Assess the user's current root route, choose required roles, then select each child's model and reasoning effort independently. Use task complexity, risk, uncertainty, concrete evidence, and confirmed launcher availability. A model name or a larger diff alone is not an escalation reason. Common combinations below are policy starting points, not measured performance equivalences or usage quotas.

## Confirm the current root

There is no mandatory root model or default Sol/high setting. Respect the user's actual selection, including a root outside the child-model registry. Confirm model and effort independently using current-turn host metadata or an accessible record for this task. Configuration defaults, the available-model list, an earlier turn, and self-description do not establish the current pair.

For a local Codex rollout, use the current task identifier supplied by the host (for example `CODEX_THREAD_ID`, with `CODEX_SESSION_ID` only when it identifies this same task). Locate that task's rollout under the configured `CODEX_HOME/sessions` directory, or `~/.codex/sessions` when unset. Read only the necessary metadata:

1. Match the current task and, when supplied, the current turn ID. Never select another task or merely the most recently modified rollout.
2. Without an explicit turn ID, require the latest `task_started` and its subsequent `turn_context` to refer to the same turn in this task's live record. An older context before the newest start is stale. If the pairing cannot be established, leave the fields unknown.
3. Read explicit `model` and `effort` fields, retaining the task/turn ID and source location as evidence. Missing or conflicting fields remain unknown; do not substitute defaults or silently resolve conflicting sources.

Refresh after a user switch and at the next material route assessment. Record confirmed fields, unknown fields, decision, suggested target, evidence, and the user's response in concise working notes. These notes are not new v3 plan or receipt fields. The validator checks child routing; it cannot authenticate root identity or guarantee that an escalation recommendation is appropriate. Unknown root metadata does not block ordinary work or explicit child selection.

## Root decisions and user choice

At initial framing and after material discovery, challenge, test, or review evidence:

- **`stay`:** retain the selected root when it can reliably frame, coordinate, and integrate the work. Terra can own ordinary engineering; Sol or Astra roots need no downgrade merely because a follow-up is easy.
- **`delegate-up`:** isolate a difficult judgment or implementation with explicit inputs, boundaries, and acceptance evidence. A Terra root may use Sol; Sol may use Astra; Terra may directly use Astra when warranted. The root must be able to integrate the result using evidence, assumptions, counterexamples, and validation, rather than treating the model name as proof. Delegation must have a distinct outcome and comply with the runtime's delegation rules.
- **`switch-root`:** recommend a stronger model, more effort on the same model, or both when the unresolved judgment is task-wide: repeated cross-phase architecture/migration decisions, tightly coupled conclusions, or final synthesis the current root cannot reliably own. State the known current configuration (including unknown fields), exact available target, concrete gap, and why bounded delegation is insufficient. Prepare a handoff containing completed work, evidence, unresolved questions, and the next step.

Do not require sequential trials through every model or effort. Evidence at task entry can justify a direct upgrade. If the current model is already the strongest confirmed option, consider supported effort, better evidence, narrower scope, or independent verification; never invent a stronger model. Do not claim that Sol/xhigh and Astra/high are equivalent, or that more effort necessarily improves a result.

`switch-root` is a recommendation, not a runtime transition. Continue already-authorized work that does not depend on an unresolved decision. A user who keeps Terra, Sol, or Astra retains that root; record the choice once and revisit only after material new evidence, scope, or an explicit request. Never hold work solely because the user did not switch. Respect explicit child-model restrictions separately from the root selection and explain any concrete unmet role/verification requirement. Only a supported, authorized runtime change followed by confirmation can be described as an actual switch; do not edit user configuration to enforce a recommendation.

TDR remains model-agnostic: its direction, confidence, risk flags, and unresolved assumptions inform AST's route choice. Missing logs, requirements, permissions, or a broken tool call first require evidence or environment repair. More expensive routing alone neither resolves them nor changes task severity or authorization requirements.

## Child model selection

| Native model (task prefix) | Default scope | Common starting effort |
| --- | --- | --- |
| `gpt-6.1-sol` (`sol`) | Ordinary engineering and critical judgment; current Sol candidate when the child launcher confirms it | `medium` for bounded engineering; `high` or `xhigh` for critical or coupled judgments |
| `gpt-6-sol` (`sol`) | Ordinary engineering and critical judgment; supported Sol fallback | `medium` for bounded engineering; `high` or `xhigh` for critical or coupled judgments |
| `gpt-6-luna` (`luna`) | Bounded all-low read-only discovery in an existing Balanced team | `high` as the current Codex starting recommendation; lower effort for simple extraction when task evidence supports it |
| `gpt-6-astra` (`astra`) | Difficult reasoning, diagnosis, design, implementation, or review that warrants the stronger model | `high` or `xhigh` for escalation assignments |
| `gpt-5.6-terra` (`terra`) | Retained ordinary implementation, QA, test strategy, design, diagnosis, and review | `medium`; `low` for explicit mechanical work, `high` for complex logic |
| `gpt-5.6-sol` (`sol`) | Retained critical engineering judgment, security review, challenge, and difficult diagnosis | `high`; `xhigh` for deeper coupled judgments |
| `gpt-5.6-luna` (`luna`) | Retained bounded all-low read-only discovery in an existing Balanced team | `low` |

These exact IDs are the approved registry, not a live availability list. Within a sufficient family, consider `gpt-6.1-sol` before `gpt-6-sol` and `gpt-5.6-sol`, and `gpt-6-luna` before `gpt-5.6-luna`, when the launcher confirms the required pair. Respect explicit user choices and comparable task evidence for another supported route. Terra remains a valid ordinary engineering route; a release alone does not make an existing route insufficient. Do not invent `gpt-6-terra`, accept arbitrary future IDs by family name, or silently rewrite an existing plan to a newer generation.

Select model eligibility first, then the lowest sufficient supported effort. Document the concrete reason a lower route is insufficient when bypassing it. Sol remains eligible for critical work; Astra is not automatically required by an Assurance label. A strong root may delegate ordinary work to Terra and bounded fact collection to Luna.

Luna duties are only `discovery`, with every assignment axis low and a fact-collection role. Do not use it for correctness/behavior judgment, public contracts, permissions, security, persisted-data semantics, migration, concurrency, deployment decisions, architecture, implementation, test strategy, or final review. A newly discovered non-low axis or wider scope causes a checkpoint and root reassignment. More effort never relaxes these boundaries.

The Luna boundary applies to both registered generations. The public model's broader coding capabilities do not expand this skill's permitted duties without a separate evaluated policy change. Both generations may use any effort allowed by the registry and confirmed by the launcher. Additional effort beyond that generation's starting point needs task evidence; simpler extraction may justify less. Terra/low, Sol/medium ordinary work, and Astra/medium bounded work remain valid when supported and sufficient. Neither eligible discovery bypasses nor uncommon pairs imply a fixed call share. When eligible Luna discovery is assigned elsewhere, explain the capability, uncertainty, risk, or user-choice reason; selecting either eligible Luna generation satisfies the family preference.

## Reasoning effort

| Effort | Selection criterion |
| --- | --- |
| `low` | Explicit extraction or mechanical rules with little inference or tradeoff |
| `medium` | Clear bounded engineering with normal implementation, testing, and edge checks |
| `high` | Complex logic, key assumptions, failure paths, state transitions, or critical judgment |
| `xhigh` | Coupled mechanisms, long deductions, conflicting evidence, difficult diagnosis, or multiple constrained alternatives |
| `max` | Exceptionally hard reasoning with adequate evidence and a concrete expected benefit from more investment |
| `ultra` | The actual launcher supports it, its orchestration behavior fits the assignment and delegation boundaries, and the task's resource constraints permit it |

The six schema values are a vocabulary, not a claim every model or endpoint supports them. API effort lists and Codex launcher options are different surfaces; API support for `none` on some models does not add it to this schema. Codex documents Ultra as using subagents, rather than simply a larger single-model reasoning budget. Before assigning it to a child, confirm that the launcher can honor the child's prohibition on further delegation; otherwise use a sufficient supported non-Ultra route. The validator checks declared values, not hidden launcher orchestration.

`gpt-6-luna` supports at most `max`; its runtime effort list and selected route must exclude `ultra`. The validator rejects that known-invalid pair even if a supplied runtime record advertises it. Other registry entries retain their existing launcher-based effort checks. Reassess effort when changing generations: the same label is not evidence of equal capability, latency, or cost. Effort is chosen for each child, never mechanically inherited from the root or derived solely from L1–L4. Routine follow-ups do not require a new team or a root setting change.

After new evidence, distinguish missing information, excessive scope, insufficient deduction, a model capability gap, and tool/environment failure. Reassign only when the evidence warrants it. Once a difficult analysis provides a validated bounded plan, later ordinary implementation may return to Terra; each verification role retains its own minimum. Stop expanding tests after required checks pass unless a change, failure, or unresolved concern justifies more.

Security Reviewer and Devil's Advocate require **a registered Sol or Astra at `high`, `xhigh`, `max`, or `ultra`**, subject to the launcher and delegation checks above. This includes both new Sol IDs and the retained `gpt-5.6-sol`. Assurance critical design, challenge, planning, and final-review judgments have the same floor, including active judgments in read-only or held plans. This is a child-role requirement, not a mandatory root setting. Test, challenge, implementation, and final-review independence remain governed by the selected mode.

## Runtime validation and fallback

`runtime.available_models` maps approved child IDs to the efforts confirmed by the current child launcher, with concrete availability evidence (at least eight visible meaningful Unicode characters per entry). Every route selects one supported pair and repeats evidence from that record. Fixture matrices, documentation, a root model picker, and a separate chat-creation tool are not child-launcher evidence. A recognized model may therefore be absent from this map. Do not copy an older generation's effort list to a newer one or use a different launcher to bypass an unavailable child route. Respect the user's route restrictions as additional constraints; never falsify availability to express a preference.

When a preferred route is absent, use another confirmed route that still meets role and effort requirements. Check all registered Sol generations and Astra before declaring a missing critical route. If none has a confirmed high-or-greater route, a critical plan may omit the unavailable specialist only as a held, write-free Assurance-critical plan declaring `runtime.unavailable_requirement: "critical-high-plus"`. The older `"sol-high-plus"` is accepted as a legacy alias for this same combined requirement; neither marker authorizes a waiver when any registered Sol or Astra high-plus route exists. Hold reasons explain the missing capability but do not authorize a waiver. Ordinary work does not hold merely because Astra or a newer Sol/Luna generation is absent.

Task names use lowercase `model_effort_purpose`: effort codes are `l`, `m`, `h`, `xh`, `mh`, and `uh`. For example `astra_xh_diagnosis` displays as `astra-XH`. Sol generations share `sol` and Luna generations share `luna`; keep purpose suffixes unique within a plan. Do not store a second display label. Plans and runtime receipts must agree on the exact child model ID, effort, and prefix. A `gpt-6-sol` receipt cannot satisfy a `gpt-6.1-sol` plan even though both use `sol`. Updating plan text does not change an already running child; use a supported reassignment and validate the next dependency wave.

Default to `fork_turns: "none"` and compact self-contained briefs. A finite-history string exactly in `"1"` through `"8"` requires `context_mode: "self-contained-finite-history"` and a concrete reason of at least eight visible meaningful Unicode characters. JSON integers, `all`, and `default` are invalid. Whitespace, controls, format characters, surrogates, and mark-only strings are not evidence.

Each child has an assignment-sized execution budget. A separate `runtime-observed` receipt with a concrete run ID may record actual calls, tokens/context, and credits; unknown values remain null. Tool calls must stay within budget. Validation checks consistency, not the authenticity of a runtime source. See [execution protocol](execution-protocol.md) and [evaluation cases](evaluation-cases.md) for dispatch and measurement.

Official guidance, checked 2026-09-30: [Codex models, rollout, and effort](https://learn.chatgpt.com/docs/models), [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol), [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), and [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra). The role limits and selection criteria above are this skill's policy, not an official performance guarantee. Validate model changes on comparable tasks before claiming quality or cost improvements.
