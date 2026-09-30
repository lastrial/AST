# Task Routing

Assess complexity, risk, and uncertainty separately as `low`, `medium`, or `high`. L1 is localized and reversible; L2 is ordinary multi-file/product work; L3 crosses modules or has material uncertainty; L4 is critical, irreversible, security-boundary, breaking compatibility, migration, or consistency work. Evidence and semantic risk override apparent diff size.

For `auto`, effective mode is the semantic minimum. A `REVISE`/`STOP` direction gate or any implementation hold makes that minimum at least Balanced, even for an all-low L1. For an explicit request, it is exactly the higher of the requested mode and that minimum: requests may escalate to safety but cannot silently downgrade or over-escalate.

| Effective mode | Required conditions and delivery gate |
| --- | --- |
| Lean | L1; all axes low; `GO`; no hold, risk flag, or architecture change. Root implements/verifies; zero children or one read-only reviewer. |
| Balanced | Ordinary L1–L3. Production work has separate implementation/review; L2/L3 also has independent test ownership. |
| Assurance | L4, high risk, `architecture`, an architecture change, or a critical flag. Separate challenge → implementation → test → final review. |

Critical flags are `security-boundary`, `compatibility-break`, `irreversible`, `data-migration`, and `distributed-consistency`. They require Assurance even if requested mode is Lean or Balanced. Architecture also requires Assurance and a Devil's Advocate.

`architecture_change` is reserved for a change to a component boundary, ownership/authority boundary, deployment topology, public contract, or long-lived data responsibility. It must carry a concrete `architecture_basis` and the `architecture` risk flag; the flag and boolean are bidirectionally consistent. Internal class or module design, dependency injection, a local abstraction, an ordinary reversible refactor, and private implementation choices are not architecture changes unless repository evidence shows one of those boundaries changes.

Canonical assessment is the axiswise maximum of the top-level assessment and every valid member `assignment_assessment`. A child with medium/high complexity or uncertainty prevents Lean; a child with `risk: high` forces Assurance, even when the top-level assessment is lower. Critical flags and architecture also force Assurance. Active delivery at that severity requires confirmed user evidence; an explicitly requested Assurance mode for otherwise low-risk work does not by itself require confirmation.

| Flag | Minimum activation |
| --- | --- |
| `architecture` | Solution Architect + Devil's Advocate |
| `public-api` | API Architect + Code Reviewer |
| `compatibility` | Solution Architect + Code Reviewer |
| `compatibility-break` | Solution Architect + Devil's Advocate + Code Reviewer |
| `database` / `data-migration` | Database Architect; migration additionally needs Migration Engineer + Devil's Advocate |
| `distributed-consistency` | Distributed Systems Architect |
| `security` / `security-boundary` / `privacy` | Security Reviewer; boundary also needs Devil's Advocate |
| `irreversible` | Project Planner + Devil's Advocate |
| `financial` | Requirements/Product owner + QA + Code Reviewer |
| `performance`, `reliability`, `accessibility` | Corresponding reviewer/SRE |
| `infrastructure`, `deployment` | DevOps; deployment also SRE |
| `frontend`, `data-pipeline`, `llm`, `rag`, `vector-db`, `storage`, `workflow`, `observability` | Corresponding named specialist |

Critical activations use their relevant duty, not merely a role label: Solution Architect `design` and Devil `challenge` for architecture; Security Reviewer `review` for a boundary; Database Architect `design`, Migration Engineer `design`, and Devil `challenge` for migration; Distributed Systems Architect `design`; Project Planner `planning` and Devil `challenge` for irreversible work; and Code Reviewer `review` where compatibility requires it.

Every triggered risk specialist is dependency-integrated, including legacy role-choice flags and Balanced compatibility work. Requirements, planning, design, and challenge precede every affected builder; test/review specialists either are the genuinely covering final Code Reviewer or cover every builder and feed that final; operations-only specialists run after it. A genuinely covering final is independent from builders and transitively consumes every builder and tester, except that Balanced may merge sequential `test` then `review` in the same QA + Code Reviewer member. Assurance always keeps test and final review independent.

`STOP` is always pending and held; reframe an accepted alternative as a new plan. Pending `REVISE` is held; confirmed `REVISE` records visible evidence and clears its direction hold. A held or read-only plan may collect bounded evidence but has no implementation, operations, or write paths. Visible text must include a meaningful Unicode character: whitespace, controls, format characters, surrogates, and mark-only strings do not count. Active delivery requires confirmed user evidence for L4, high assessed risk, architecture, or any critical flag (`security-boundary`, `compatibility-break`, `irreversible`, `data-migration`, or `distributed-consistency`). A listed risk role only activates when its own allowed duty is present; an inert secondary role is not evidence.

Model and effort recommendations do not themselves change complexity, risk, mode, or confirmation requirements. Reuse prior authorization where it covers the accepted direction; routine implementation choices do not create a new confirmation gate. Respect a user's retained root configuration and continue work that does not depend on an unresolved decision.

When no registered Sol generation or Astra has a confirmed high-or-greater route, a critical plan may be represented only as a held, write-free plan with `runtime.unavailable_requirement: "critical-high-plus"` and evidence showing the missing capability. The legacy `"sol-high-plus"` alias has the same combined meaning and cannot waive a specialist when any registered Sol or Astra high-or-greater route is available. Hold reasons remain explanatory. Once a safe route exists, normal activation and role/effort checks apply.
