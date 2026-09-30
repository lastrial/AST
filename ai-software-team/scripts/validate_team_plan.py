#!/usr/bin/env python3
"""Strict, fail-closed validator for AI Software Team schema v3."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any

LEVELS = {"L1", "L2", "L3", "L4"}
ASSESSMENTS = {"low", "medium", "high"}
GATES = {"GO", "REVISE", "STOP"}
CONFIRMATIONS = {"not-required", "pending", "confirmed"}
SCOPES = {"delivery", "read-only"}
EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}
EFFORT_CODES = {"low": "l", "medium": "m", "high": "h", "xhigh": "xh", "max": "mh", "ultra": "uh"}
FINITE_HISTORY_TURNS = {str(value) for value in range(1, 9)}
MODE_ORDER = {"lean": 1, "balanced": 2, "assurance": 3}
ASSESSMENT_ORDER = {"low": 1, "medium": 2, "high": 3}
MODE_REQUESTS = {"auto", *MODE_ORDER}
CRITICAL_ROUTE_EFFORTS = {"high", "xhigh", "max", "ultra"}
CRITICAL_UNAVAILABLE_REQUIREMENTS = {"critical-high-plus", "sol-high-plus"}
CRITICAL_SPECIALIST_LABELS = {"security_reviewer": "Security Reviewer", "devils_advocate": "Devil's Advocate"}
ASSURANCE_CRITICAL_ROLES = {
    "devils_advocate", "security_reviewer", "code_reviewer", "solution_architect", "database_architect",
    "distributed_systems_architect", "project_planner", "migration_engineer",
}
CRITICAL_JUDGMENT_DUTIES = {"planning", "challenge", "design", "review"}
LUNA_DISCOVERY_ROLES = {"repository_analyst"}
CRITICAL_FLAGS = {"security-boundary", "compatibility-break", "irreversible", "data-migration", "distributed-consistency"}
RISK_FLAGS = {
    "architecture", "public-api", "compatibility", "compatibility-break", "database", "data-migration", "distributed-consistency",
    "security", "security-boundary", "privacy", "financial", "irreversible", "performance", "reliability", "infrastructure",
    "deployment", "frontend", "accessibility", "data-pipeline", "llm", "rag", "vector-db", "storage", "workflow", "observability",
}
TOP_FIELDS = {"version", "task_level", "assessment", "outcome", "hard_constraints", "proposed_method", "assumptions", "acceptance_criteria", "architecture_change", "architecture_basis", "direction_gate", "user_confirmation", "confirmation_evidence", "implementation_hold", "hold_reasons", "risk_flags", "evidence", "mode", "runtime", "execution_scope", "members"}
MODE_FIELDS = {"requested", "effective", "reasons"}
RUNTIME_FIELDS = {"available_models", "availability_evidence", "unavailable_requirement"}
MEMBER_FIELDS = {"task_name", "roles", "duties", "wave", "reason", "owns", "write_paths", "deliverable", "depends_on", "assignment_assessment", "route", "delegation", "execution_budget"}
ASSESSMENT_FIELDS = {"complexity", "risk", "uncertainty"}
ROUTE_FIELDS = {"model", "effort", "fork_turns", "context_mode", "selection_reason", "availability_evidence", "finite_history_reason"}
ARCHITECTURE_BASIS_FIELDS = {"categories", "rationale"}
ARCHITECTURE_CATEGORIES = {"component-boundary", "ownership-authority", "deployment-topology", "public-contract", "long-lived-data-responsibility"}
DELEGATION_FIELDS = {"invoke_ast", "spawn_subagents", "ast_access", "ast_maintenance_targets"}
AST_ACCESS = {"forbidden", "explicit-maintenance-targets"}
AST_MAINTENANCE_TARGETS = {
    "SKILL.md", "agents/openai.yaml", "references/task-routing.md", "references/execution-protocol.md",
    "references/model-routing.md", "references/evaluation-cases.md", "references/role-catalog.md",
    "scripts/validate_team_plan.py", "scripts/test_validate_team_plan.py",
}
EXECUTION_BUDGET_FIELDS = {"max_tool_calls", "max_followups", "max_evidence_items", "no_progress_limit"}
RECEIPT_FIELDS = {"source", "run_id", "members"}
RECEIPT_MEMBER_FIELDS = {"task_name", "actual_model", "actual_effort", "followup_count", "tool_calls", "model_calls", "input_tokens", "cached_input_tokens", "output_tokens", "max_context_tokens", "credits"}
RECEIPT_INTEGER_METRICS = {"tool_calls", "model_calls", "input_tokens", "cached_input_tokens", "output_tokens", "max_context_tokens"}
ALLOWED_DUTIES = {"discovery", "requirements", "planning", "challenge", "design", "implementation", "test", "review", "operations", "integration"}
# Exact launcher IDs only.  Recognition here grants no availability: every
# route still needs the exact model/effort pair recorded by the runtime.
MODEL_POLICY = {
    "gpt-5.6-sol": {"prefix": "sol", "duties": ALLOWED_DUTIES, "critical": True, "advertised_efforts": EFFORTS},
    "gpt-6.1-sol": {"prefix": "sol", "duties": ALLOWED_DUTIES, "critical": True, "advertised_efforts": EFFORTS},
    "gpt-6-sol": {"prefix": "sol", "duties": ALLOWED_DUTIES, "critical": True, "advertised_efforts": EFFORTS},
    "gpt-5.6-terra": {"prefix": "terra", "duties": ALLOWED_DUTIES, "critical": False, "advertised_efforts": EFFORTS},
    "gpt-5.6-luna": {"prefix": "luna", "duties": {"discovery"}, "critical": False, "advertised_efforts": EFFORTS},
    "gpt-6-luna": {"prefix": "luna", "duties": {"discovery"}, "critical": False, "advertised_efforts": EFFORTS - {"ultra"}},
    "gpt-6-astra": {"prefix": "astra", "duties": ALLOWED_DUTIES, "critical": True, "advertised_efforts": EFFORTS},
}
NATIVE_MODELS = {model: policy["prefix"] for model, policy in MODEL_POLICY.items()}
MODEL_DUTIES = {model: policy["duties"] for model, policy in MODEL_POLICY.items()}
CRITICAL_ROUTE_MODELS = {model for model, policy in MODEL_POLICY.items() if policy["critical"]}
LUNA_MODELS = tuple(model for model, policy in MODEL_POLICY.items() if policy["prefix"] == "luna")
ROLE_DUTIES = {
    "engineering_manager": {"planning", "integration"}, "product_manager": {"requirements"}, "requirements_analyst": {"requirements"},
    "project_planner": {"planning", "integration"}, "repository_analyst": {"discovery"}, "solution_architect": {"design", "integration"},
    "backend_architect": {"design"}, "frontend_architect": {"design"}, "api_architect": {"design"}, "database_architect": {"design"},
    "distributed_systems_architect": {"design"}, "cloud_architect": {"design"}, "backend_developer": {"implementation"},
    "frontend_developer": {"design", "implementation"}, "mobile_developer": {"design", "implementation"},
    "devops_engineer": {"design", "implementation", "operations"}, "site_reliability_engineer": {"design", "review", "operations"},
    "release_engineer": {"planning", "implementation", "operations", "integration"}, "data_engineer": {"design", "implementation", "test", "operations"},
    "ml_engineer": {"design", "implementation", "test"}, "migration_engineer": {"design", "implementation", "test", "operations"},
    "qa_engineer": {"test"}, "test_automation_engineer": {"test"}, "code_reviewer": {"review"}, "security_reviewer": {"review"},
    "performance_reviewer": {"review"}, "accessibility_reviewer": {"review"}, "rag_architect": {"design"},
    "llm_engineer": {"design", "implementation", "test"}, "vector_database_engineer": {"design", "implementation", "test", "operations"},
    "storage_engineer": {"design", "implementation", "test", "operations"}, "workflow_engineer": {"design", "implementation", "test"},
    "observability_engineer": {"design", "implementation", "test", "review", "operations"},
    "developer_experience_engineer": {"design", "implementation", "test"}, "devils_advocate": {"challenge"},
}
RISK_ROLE_REQUIREMENTS = {
    "architecture": [{"solution_architect"}, {"devils_advocate"}], "public-api": [{"api_architect"}, {"code_reviewer"}],
    "compatibility": [{"solution_architect"}, {"code_reviewer"}], "compatibility-break": [{"solution_architect"}, {"devils_advocate"}, {"code_reviewer"}],
    "database": [{"database_architect"}], "data-migration": [{"database_architect"}, {"migration_engineer"}, {"devils_advocate"}],
    "distributed-consistency": [{"distributed_systems_architect"}], "security": [{"security_reviewer"}],
    "security-boundary": [{"security_reviewer"}, {"devils_advocate"}], "privacy": [{"security_reviewer"}],
    "financial": [{"requirements_analyst", "product_manager"}, {"qa_engineer"}, {"code_reviewer"}], "irreversible": [{"project_planner"}, {"devils_advocate"}],
    "performance": [{"performance_reviewer"}], "reliability": [{"site_reliability_engineer"}], "infrastructure": [{"devops_engineer"}],
    "deployment": [{"devops_engineer"}, {"site_reliability_engineer"}], "frontend": [{"frontend_developer"}],
    "accessibility": [{"accessibility_reviewer"}], "data-pipeline": [{"data_engineer"}], "llm": [{"llm_engineer"}],
    "rag": [{"rag_architect"}], "vector-db": [{"vector_database_engineer"}], "storage": [{"storage_engineer"}],
    "workflow": [{"workflow_engineer"}], "observability": [{"observability_engineer"}],
}
FLAG_ROLE_DUTY_REQUIREMENTS = {
    "architecture": [("solution_architect", "design"), ("devils_advocate", "challenge")],
    "public-api": [("api_architect", "design"), ("code_reviewer", "review")],
    "compatibility": [("solution_architect", "design"), ("code_reviewer", "review")],
    "compatibility-break": [("solution_architect", "design"), ("devils_advocate", "challenge"), ("code_reviewer", "review")],
    "security-boundary": [("security_reviewer", "review"), ("devils_advocate", "challenge")],
    "data-migration": [("database_architect", "design"), ("migration_engineer", "design"), ("devils_advocate", "challenge")],
    "distributed-consistency": [("distributed_systems_architect", "design")],
    "irreversible": [("project_planner", "planning"), ("devils_advocate", "challenge")],
}


def load_catalog_ids(path: Path) -> set[str]:
    """Read role IDs from the single-role catalog table deterministically."""
    return set(re.findall(r"^\| `([a-z_]+)` \|", path.read_text(encoding="utf-8"), re.MULTILINE))


def load_catalog_duties(path: Path) -> dict[str, set[str]]:
    """Read the catalog's documented duty sets for deterministic sync tests."""
    rows = re.findall(r"^\| `([a-z_]+)` \| (.+?) \|$", path.read_text(encoding="utf-8"), re.MULTILINE)
    result: dict[str, set[str]] = {}
    for role, duties in rows:
        cleaned = re.sub(r" \([^)]*\)", "", duties)
        result[role] = {duty.strip() for duty in cleaned.split(",")}
    return result


def _one(value: Any, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices


def _critical_route_available(available: dict[str, set[str]]) -> bool:
    """Whether launcher evidence confirms any safe critical route."""
    return any(available.get(model, set()) & CRITICAL_ROUTE_EFFORTS for model in CRITICAL_ROUTE_MODELS)


def _require_critical_route(errors: list[str], label: str, route: dict[str, Any]) -> None:
    if not _one(route.get("model"), CRITICAL_ROUTE_MODELS):
        errors.append(f"{label} requires Sol or Astra")
    if not _one(route.get("effort"), CRITICAL_ROUTE_EFFORTS):
        errors.append(f"{label} requires high or greater effort")


def _text(value: Any) -> bool:
    """Accept text only when it contains a visible, meaningful character.

    Whitespace, controls, format characters, surrogates, and combining marks
    cannot stand in for evidence or a human-readable reason.  Combining marks
    remain valid within otherwise visible Unicode text.
    """
    return isinstance(value, str) and _meaningful_length(value) > 0


def _meaningful_length(value: Any) -> int:
    if not isinstance(value, str):
        return 0
    return sum(
        not character.isspace()
        and unicodedata.category(character) not in {"Cc", "Cf", "Cs", "Mn", "Mc", "Me"}
        for character in value
    )


def _strings(value: Any, label: str, errors: list[str], *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value) or any(not _text(item) for item in value):
        errors.append(f"{label} must be {'a non-empty ' if nonempty else 'a '}list of non-empty strings")
        return []
    return value


def _safe_strings(value: Any) -> list[str]:
    """Return only string entries; downstream validation must never trust JSON shape."""
    return value if isinstance(value, list) and all(isinstance(item, str) for item in value) else []


def _object(value: Any, allowed: set[str], label: str, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return None
    errors.extend(f"{label}.{key} is unknown in schema v3" for key in value if key not in allowed)
    return value


def _requires_high_risk_confirmation(level: Any, assessment: Any, flags: list[str], architecture_change: Any) -> bool:
    safe_assessment = assessment if isinstance(assessment, dict) else {}
    risk = safe_assessment.get("risk") if isinstance(safe_assessment.get("risk"), str) else None
    flag_set = set(flags)
    return level == "L4" or risk == "high" or bool(flag_set & CRITICAL_FLAGS) or "architecture" in flag_set or architecture_change is True


def _semantic_minimum(level: Any, assessment: Any, flags: list[str], architecture_change: Any, direction_gate: Any, implementation_hold: Any) -> str:
    safe_assessment = assessment if isinstance(assessment, dict) else {}
    if _requires_high_risk_confirmation(level, safe_assessment, flags, architecture_change):
        return "assurance"
    axes = [safe_assessment.get(axis) if isinstance(safe_assessment.get(axis), str) else None for axis in ASSESSMENT_FIELDS]
    if (isinstance(level, str) and level in {"L2", "L3"}) or any(axis != "low" for axis in axes) or flags or (isinstance(direction_gate, str) and direction_gate in {"REVISE", "STOP"}) or implementation_hold is True:
        return "balanced"
    return "lean"


def _aggregate_assessment(top_level: Any, members: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Compute the axiswise maximum using only structurally valid assessment values."""
    aggregate = {axis: "low" for axis in ASSESSMENT_FIELDS}
    candidates = [top_level] + [item.get("assignment_assessment") for item in members.values()]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for axis in ASSESSMENT_FIELDS:
            value = candidate.get(axis)
            if _one(value, ASSESSMENTS) and ASSESSMENT_ORDER[value] > ASSESSMENT_ORDER[aggregate[axis]]:
                aggregate[axis] = value
    return aggregate


def load_plan_json(text: str) -> Any:
    """Parse plan JSON strictly: duplicate keys and non-finite values are invalid."""
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON object key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON value: {value}")

    def reject_nonfinite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError(f"non-finite JSON number: {value}")
        return parsed

    return json.loads(text, object_pairs_hook=reject_duplicates, parse_constant=reject_constant, parse_float=reject_nonfinite_float)


def _has_path(members: dict[str, dict[str, Any]], target: str, source: str) -> bool:
    item = members.get(target, {})
    pending = list(item.get("depends_on", [])) if isinstance(item.get("depends_on"), list) else []
    seen: set[str] = set()
    while pending:
        current = pending.pop()
        if current == source:
            return True
        if isinstance(current, str) and current in members and current not in seen:
            seen.add(current)
            dependencies = members[current].get("depends_on", [])
            if isinstance(dependencies, list):
                pending.extend(dependencies)
    return False


def _active_duties_for_role(item: dict[str, Any], role: str) -> set[str]:
    """Return only duties that make this particular role active."""
    if role not in _safe_strings(item.get("roles")):
        return set()
    return set(_safe_strings(item.get("duties"))) & ROLE_DUTIES.get(role, set())


def _combined_test_review_is_sequential(item: dict[str, Any]) -> bool:
    duties = _safe_strings(item.get("duties"))
    return "test" in duties and "review" in duties and duties.index("test") < duties.index("review")


def _genuinely_covering_final(
    item: dict[str, Any],
    members: dict[str, dict[str, Any]],
    builders: list[dict[str, Any]],
    testers: list[dict[str, Any]],
    effective: str | None,
) -> bool:
    """A final reviewer independently consumes the complete build/test chain."""
    name = item.get("task_name")
    if not isinstance(name, str) or item in builders:
        return False
    if any(not isinstance(builder.get("task_name"), str) or not _has_path(members, name, builder["task_name"]) for builder in builders):
        return False
    for tester in testers:
        tester_name = tester.get("task_name")
        if tester is item:
            if effective != "balanced" or not _combined_test_review_is_sequential(item):
                return False
        elif not isinstance(tester_name, str) or not _has_path(members, name, tester_name):
            return False
    return True


def _triggered_specialists(
    flags: list[str], members: dict[str, dict[str, Any]]
) -> list[tuple[str, dict[str, Any], set[str]]]:
    """Return every active member that satisfies a triggered risk requirement.

    Exact requirements intentionally retain their specified duty.  Older
    role-choice requirements derive the active duty from each matching role.
    The representation is shared by all dependency-integration checks.
    """
    result: list[tuple[str, dict[str, Any], set[str]]] = []
    for flag in flags:
        exact = FLAG_ROLE_DUTY_REQUIREMENTS.get(flag)
        if exact is not None:
            for role, duty in exact:
                for item in members.values():
                    if duty in _active_duties_for_role(item, role):
                        result.append((flag, item, {duty}))
            continue
        for choices in RISK_ROLE_REQUIREMENTS.get(flag, []):
            for item in members.values():
                duties: set[str] = set()
                for role in choices:
                    duties |= _active_duties_for_role(item, role)
                if duties:
                    result.append((flag, item, duties))
    return result


def _valid_write_path(path: Any) -> bool:
    if not _text(path) or path.startswith("/") or "\\" in path or any(character in path for character in "*?[]{}") or any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in path):
        return False
    candidate = PurePosixPath(path)
    return path != "." and all(part not in {"", ".", ".."} for part in candidate.parts) and str(candidate) == path


def _ancestor(left: str, right: str) -> bool:
    canonical_left = unicodedata.normalize("NFC", left.casefold())
    canonical_right = unicodedata.normalize("NFC", right.casefold())
    return canonical_left == canonical_right or canonical_right.startswith(canonical_left + "/") or canonical_left.startswith(canonical_right + "/")


def _wave(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 1 else None


def _nonnegative_number_or_null(value: Any) -> bool:
    return value is None or (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0)


def _nonnegative_integer_or_null(value: Any) -> bool:
    return value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 0)


def validate_receipt(plan: Any, receipt: Any) -> list[str]:
    """Validate supplied runtime observations without claiming they are authentic."""
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return ["receipt must be a JSON object"]
    _object(receipt, RECEIPT_FIELDS, "receipt", errors)
    for field in RECEIPT_FIELDS:
        if field not in receipt:
            errors.append(f"receipt.{field} is required")
    if receipt.get("source") != "runtime-observed":
        errors.append("receipt.source must be runtime-observed")
    if _meaningful_length(receipt.get("run_id")) < 3:
        errors.append("receipt.run_id must be a concrete visible string")

    plan_members = plan.get("members") if isinstance(plan, dict) and isinstance(plan.get("members"), list) else []
    routes: dict[str, dict[str, Any]] = {}
    for member in plan_members:
        if isinstance(member, dict) and isinstance(member.get("task_name"), str) and isinstance(member.get("route"), dict):
            routes[member["task_name"]] = member["route"]

    receipt_members = receipt.get("members")
    if not isinstance(receipt_members, list):
        errors.append("receipt.members must be a list")
        return errors
    seen: set[str] = set()
    for index, item in enumerate(receipt_members):
        label = f"receipt.members[{index}]"
        item = _object(item, RECEIPT_MEMBER_FIELDS, label, errors)
        if item is None:
            continue
        for field in RECEIPT_MEMBER_FIELDS:
            if field not in item:
                errors.append(f"{label}.{field} is required")
        name = item.get("task_name")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            errors.append(f"{label}.task_name must use lowercase letters, digits, and underscores")
            continue
        if name in seen:
            errors.append(f"duplicate receipt task_name: {name}")
            continue
        seen.add(name)
        route = routes.get(name)
        if route is None:
            errors.append(f"receipt member {name} is not in plan")
        else:
            if item.get("actual_model") != route.get("model"):
                errors.append(f"receipt member {name} actual_model must match plan route")
            if item.get("actual_effort") != route.get("effort"):
                errors.append(f"receipt member {name} actual_effort must match plan route")
            model, effort = item.get("actual_model"), item.get("actual_effort")
            if isinstance(model, str) and model in NATIVE_MODELS and _one(effort, EFFORTS):
                prefix = f"{NATIVE_MODELS[model]}_{EFFORT_CODES[effort]}_"
                if not name.startswith(prefix) or len(name) == len(prefix):
                    errors.append(f"receipt member {name} must match actual model/effort prefix")
        followups = item.get("followup_count")
        if not isinstance(followups, int) or isinstance(followups, bool) or followups < 0:
            errors.append(f"{label}.followup_count must be a non-negative integer")
        elif route is not None:
            budget = next((member.get("execution_budget") for member in plan_members if isinstance(member, dict) and member.get("task_name") == name), None)
            if isinstance(budget, dict) and isinstance(budget.get("max_followups"), int) and followups > budget["max_followups"]:
                errors.append(f"receipt member {name} followup_count exceeds plan budget")
        for metric in RECEIPT_INTEGER_METRICS:
            if not _nonnegative_integer_or_null(item.get(metric)):
                errors.append(f"{label}.{metric} must be a non-negative integer or null")
        if not _nonnegative_number_or_null(item.get("credits")):
            errors.append(f"{label}.credits must be a non-negative number or null")
        tool_calls = item.get("tool_calls")
        if route is not None and isinstance(tool_calls, int) and not isinstance(tool_calls, bool):
            budget = next((member.get("execution_budget") for member in plan_members if isinstance(member, dict) and member.get("task_name") == name), None)
            if isinstance(budget, dict) and isinstance(budget.get("max_tool_calls"), int) and tool_calls > budget["max_tool_calls"]:
                errors.append(f"receipt member {name} tool_calls exceeds plan budget")
    missing = set(routes) - seen
    if missing:
        errors.append(f"receipt is missing plan members: {', '.join(sorted(missing))}")
    return errors


def validate(plan: Any, catalog_ids: set[str] | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, dict):
        return ["plan must be a JSON object"], warnings
    if isinstance(plan.get("version"), int) and not isinstance(plan.get("version"), bool) and plan.get("version") in {1, 2}:
        return ["schema v3 migration required: v1/v2 plans are explicitly unsupported"], warnings
    _object(plan, TOP_FIELDS, "plan", errors)
    if plan.get("version") != 3: errors.append("version must be 3")
    for field in TOP_FIELDS - {"proposed_method"}:
        if field not in plan: errors.append(f"plan.{field} is required")
    if not _one(plan.get("task_level"), LEVELS): errors.append("task_level must be L1, L2, L3, or L4")
    if not _one(plan.get("execution_scope"), SCOPES): errors.append("execution_scope must be delivery or read-only")
    if not _text(plan.get("outcome")): errors.append("outcome must be a non-empty string")
    if plan.get("proposed_method") is not None and not _text(plan.get("proposed_method")): errors.append("proposed_method must be null or a non-empty string")
    for field in ("hard_constraints", "assumptions", "acceptance_criteria", "evidence", "hold_reasons", "risk_flags"):
        _strings(plan.get(field), field, errors)
    if not isinstance(plan.get("architecture_change"), bool): errors.append("architecture_change must be boolean")
    architecture_basis = plan.get("architecture_basis")
    if plan.get("architecture_change") is False:
        if architecture_basis is not None: errors.append("architecture_basis must be null when architecture_change is false")
    elif plan.get("architecture_change") is True:
        basis = _object(architecture_basis, ARCHITECTURE_BASIS_FIELDS, "architecture_basis", errors)
        if basis is not None:
            for field in ARCHITECTURE_BASIS_FIELDS:
                if field not in basis: errors.append(f"architecture_basis.{field} is required")
            categories = basis.get("categories")
            if not isinstance(categories, list) or not categories or any(not isinstance(category, str) or category not in ARCHITECTURE_CATEGORIES for category in categories) or len(set(categories)) != len(categories):
                errors.append("architecture_basis.categories must be a non-empty unique architecture category array")
            if _meaningful_length(basis.get("rationale")) < 8:
                errors.append("architecture_basis.rationale must be concrete visible text")
    if not _one(plan.get("direction_gate"), GATES): errors.append("direction_gate must be GO, REVISE, or STOP")
    if not _one(plan.get("user_confirmation"), CONFIRMATIONS): errors.append("user_confirmation is invalid")
    if not isinstance(plan.get("implementation_hold"), bool): errors.append("implementation_hold must be boolean")

    raw_flags = plan.get("risk_flags", [])
    flags = raw_flags if isinstance(raw_flags, list) and all(isinstance(flag, str) for flag in raw_flags) else []
    for flag in flags:
        if flag not in RISK_FLAGS: errors.append(f"unknown risk flag: {flag}")
    if plan.get("architecture_change") is True and "architecture" not in flags: errors.append("architecture_change requires the architecture risk flag")
    if "architecture" in flags and plan.get("architecture_change") is not True: errors.append("architecture risk flag requires architecture_change")
    hold_reasons = plan.get("hold_reasons", [])
    has_reasons = isinstance(hold_reasons, list) and bool(hold_reasons) and all(_text(reason) for reason in hold_reasons)
    if isinstance(plan.get("implementation_hold"), bool) and plan["implementation_hold"] != has_reasons:
        errors.append("implementation_hold must exactly match non-empty hold_reasons")
    confirmation = plan.get("user_confirmation")
    confirmation_evidence = plan.get("confirmation_evidence")
    if confirmation == "confirmed":
        _strings(confirmation_evidence, "confirmation_evidence", errors, nonempty=True)
    elif confirmation_evidence is not None:
        errors.append("confirmation_evidence must be null unless confirmation is confirmed")
    gate = plan.get("direction_gate")
    if gate == "STOP":
        if confirmation != "pending" or plan.get("implementation_hold") is not True:
            errors.append("STOP must be pending and held; accepted alternatives need a reframed plan")
    elif gate == "REVISE":
        if confirmation == "pending" and plan.get("implementation_hold") is not True:
            errors.append("pending REVISE must be held")
        if confirmation == "confirmed" and (plan.get("implementation_hold") is not False or hold_reasons):
            errors.append("confirmed REVISE must clear the direction hold before delivery")
        if confirmation == "not-required": errors.append("REVISE requires pending or confirmed user confirmation")
    elif gate == "GO" and confirmation == "pending":
        errors.append("GO cannot have pending direction confirmation")

    assessment = _object(plan.get("assessment"), ASSESSMENT_FIELDS, "assessment", errors)
    if assessment is not None:
        for axis in ASSESSMENT_FIELDS:
            if not _one(assessment.get(axis), ASSESSMENTS): errors.append(f"assessment.{axis} must be low, medium, or high")
    mode = _object(plan.get("mode"), MODE_FIELDS, "mode", errors)
    effective: str | None = None
    semantic_minimum = _semantic_minimum(plan.get("task_level"), assessment, flags, plan.get("architecture_change"), gate, plan.get("implementation_hold"))
    if mode is not None:
        requested, effective = mode.get("requested"), mode.get("effective")
        if not _one(requested, MODE_REQUESTS): errors.append("mode.requested is invalid")
        if not _one(effective, set(MODE_ORDER)): errors.append("mode.effective is invalid")
        _strings(mode.get("reasons"), "mode.reasons", errors, nonempty=True)

    runtime = _object(plan.get("runtime"), RUNTIME_FIELDS, "runtime", errors)
    available: dict[str, set[str]] = {}
    runtime_evidence: list[str] = []
    unavailable_requirement: Any = None
    if runtime is not None:
        models = runtime.get("available_models")
        if not isinstance(models, dict): errors.append("runtime.available_models must be a mapping")
        else:
            for model, efforts in models.items():
                if not isinstance(model, str) or model not in NATIVE_MODELS:
                    errors.append(f"runtime.available_models contains unsupported native model {model}")
                elif (
                    not isinstance(efforts, list)
                    or not efforts
                    or any(not _one(effort, MODEL_POLICY[model]["advertised_efforts"]) for effort in efforts)
                    or len(set(efforts)) != len(efforts)
                ):
                    errors.append(f"runtime.available_models.{model} must be a non-empty unique supported effort array")
                else:
                    available[model] = set(efforts)
        runtime_evidence = _strings(runtime.get("availability_evidence"), "runtime.availability_evidence", errors, nonempty=True)
        if runtime_evidence and any(_meaningful_length(entry) < 8 for entry in runtime_evidence):
            errors.append("runtime.availability_evidence must contain concrete visible evidence of at least eight characters")
        unavailable_requirement = runtime.get("unavailable_requirement")
        if unavailable_requirement is not None and not _one(unavailable_requirement, CRITICAL_UNAVAILABLE_REQUIREMENTS):
            errors.append("runtime.unavailable_requirement must be null, critical-high-plus, or legacy sol-high-plus")

    raw_members = plan.get("members")
    if not isinstance(raw_members, list): errors.append("members must be a list"); raw_members = []
    members: dict[str, dict[str, Any]] = {}
    all_write_paths: list[tuple[str, str]] = []
    for index, item in enumerate(raw_members):
        label = f"members[{index}]"
        item = _object(item, MEMBER_FIELDS, label, errors)
        if item is None: continue
        for field in MEMBER_FIELDS:
            if field not in item: errors.append(f"{label}.{field} is required")
        name, roles, duties = item.get("task_name"), item.get("roles"), item.get("duties")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name): errors.append(f"{label}.task_name must use lowercase letters, digits, and underscores")
        elif name in members: errors.append(f"duplicate task_name: {name}")
        else: members[name] = item
        valid_roles = isinstance(roles, list) and 1 <= len(roles) <= 2 and all(isinstance(role, str) and role in ROLE_DUTIES for role in roles)
        valid_duties = isinstance(duties, list) and bool(duties) and all(isinstance(duty, str) and duty in ALLOWED_DUTIES for duty in duties)
        if not valid_roles: errors.append(f"{label}.roles must contain one or two known roles")
        elif len(set(roles)) != len(roles): errors.append(f"{label}.roles cannot contain duplicates")
        elif "engineering_manager" in roles: errors.append(f"{label} cannot declare engineering_manager")
        if not valid_duties: errors.append(f"{label}.duties must be non-empty known duties")
        elif len(set(duties)) != len(duties): errors.append(f"{label}.duties cannot contain duplicates")
        # Do not touch a set or membership operation until both JSON arrays are
        # fully validated strings.  This is intentionally stricter than merely
        # checking that they are lists: nested dict/list entries are unhashable.
        if valid_roles and valid_duties:
            allowed = set().union(*(ROLE_DUTIES[role] for role in roles))
            errors.extend(f"{label}: duty {duty} does not match declared roles" for duty in duties if duty not in allowed)
            for role in roles:
                if not set(duties) & ROLE_DUTIES[role]: errors.append(f"{label}: role {role} has no active declared duty")
        if not isinstance(item.get("wave"), int) or isinstance(item.get("wave"), bool) or item["wave"] < 1: errors.append(f"{label}.wave must be a positive integer")
        for field in ("reason", "deliverable"):
            if not _text(item.get(field)): errors.append(f"{label}.{field} must be a non-empty string")
        _strings(item.get("owns"), f"{label}.owns", errors, nonempty=True)
        write_paths = _strings(item.get("write_paths"), f"{label}.write_paths", errors)
        _strings(item.get("depends_on"), f"{label}.depends_on", errors)
        has_implementation = isinstance(duties, list) and "implementation" in duties
        if has_implementation and not write_paths: errors.append(f"{label} implementation requires write_paths")
        if write_paths and not has_implementation: errors.append(f"{label} only implementation duty may own write_paths")
        declared_duties = set(_safe_strings(duties))
        if {"challenge", "review"} & declared_duties and {"implementation", "operations"} & declared_duties:
            errors.append(f"{label} challenge/review duties cannot combine with implementation or operations")
        if {"challenge", "review"} & declared_duties and write_paths:
            errors.append(f"{label} challenge/review duties must be read-only")
        for path in write_paths:
            if not _valid_write_path(path): errors.append(f"{label}.write_paths contains unsafe or non-normalized path {path!r}")
            else:
                conflicts = [owner for existing, owner in all_write_paths if _ancestor(path, existing)]
                if conflicts: errors.append(f"write_path {path} overlaps existing owner {conflicts[0]}")
                all_write_paths.append((path, str(name)))
        assignment = _object(item.get("assignment_assessment"), ASSESSMENT_FIELDS, f"{label}.assignment_assessment", errors)
        if assignment is not None:
            for axis in ASSESSMENT_FIELDS:
                if not _one(assignment.get(axis), ASSESSMENTS): errors.append(f"{label}.assignment_assessment.{axis} is invalid")
        delegation = _object(item.get("delegation"), DELEGATION_FIELDS, f"{label}.delegation", errors)
        if delegation is not None:
            for field in DELEGATION_FIELDS:
                if field not in delegation: errors.append(f"{label}.delegation.{field} is required")
            if delegation.get("invoke_ast") is not False: errors.append(f"{label}.delegation.invoke_ast must be false")
            if delegation.get("spawn_subagents") is not False: errors.append(f"{label}.delegation.spawn_subagents must be false")
            access = delegation.get("ast_access")
            if access not in AST_ACCESS: errors.append(f"{label}.delegation.ast_access is invalid")
            targets = delegation.get("ast_maintenance_targets")
            valid_targets = isinstance(targets, list) and all(isinstance(target, str) and target in AST_MAINTENANCE_TARGETS for target in targets)
            if not valid_targets:
                errors.append(f"{label}.delegation.ast_maintenance_targets must be approved Skill-relative AST artifacts")
            elif len(set(targets)) != len(targets):
                errors.append(f"{label}.delegation.ast_maintenance_targets must be unique")
            elif access == "forbidden" and targets:
                errors.append(f"{label}.delegation.ast_access forbidden requires empty ast_maintenance_targets")
            elif access == "explicit-maintenance-targets" and not targets:
                errors.append(f"{label}.delegation.ast_access explicit-maintenance-targets requires non-empty ast_maintenance_targets")
        budget = _object(item.get("execution_budget"), EXECUTION_BUDGET_FIELDS, f"{label}.execution_budget", errors)
        if budget is not None:
            for field in EXECUTION_BUDGET_FIELDS:
                if field not in budget: errors.append(f"{label}.execution_budget.{field} is required")
            max_tools, max_followups = budget.get("max_tool_calls"), budget.get("max_followups")
            max_evidence, no_progress = budget.get("max_evidence_items"), budget.get("no_progress_limit")
            if not isinstance(max_tools, int) or isinstance(max_tools, bool) or not 1 <= max_tools <= 64: errors.append(f"{label}.execution_budget.max_tool_calls must be an integer from 1 through 64")
            if not isinstance(max_followups, int) or isinstance(max_followups, bool) or not 0 <= max_followups <= 3: errors.append(f"{label}.execution_budget.max_followups must be an integer from 0 through 3")
            if not isinstance(max_evidence, int) or isinstance(max_evidence, bool) or not 1 <= max_evidence <= 20: errors.append(f"{label}.execution_budget.max_evidence_items must be an integer from 1 through 20")
            if not isinstance(no_progress, int) or isinstance(no_progress, bool) or not 1 <= no_progress <= 5 or (isinstance(max_tools, int) and not isinstance(max_tools, bool) and no_progress > max_tools): errors.append(f"{label}.execution_budget.no_progress_limit must be an integer from 1 through 5 and no greater than max_tool_calls")
        route = _object(item.get("route"), ROUTE_FIELDS, f"{label}.route", errors)
        if route is None: continue
        for field in ROUTE_FIELDS - {"finite_history_reason"}:
            if field not in route: errors.append(f"{label}.route.{field} is required")
        model, effort = route.get("model"), route.get("effort")
        if not isinstance(model, str) or model not in available: errors.append(f"{label}.route.model must be runtime-confirmed native model")
        if not _one(effort, EFFORTS): errors.append(f"{label}.route.effort must be one of the six explicit efforts")
        elif isinstance(model, str) and model in MODEL_POLICY and effort not in MODEL_POLICY[model]["advertised_efforts"]: errors.append(f"{label}.route.effort is not supported for {model}")
        elif isinstance(model, str) and model in available and effort not in available[model]: errors.append(f"{label}.route.effort is not confirmed for {model}")
        if isinstance(name, str) and isinstance(model, str) and model in NATIVE_MODELS and _one(effort, EFFORTS):
            prefix = f"{NATIVE_MODELS[model]}_{EFFORT_CODES[effort]}_"
            if not name.startswith(prefix) or len(name) == len(prefix): errors.append(f"{label}.task_name must start with {prefix}")
        fork = route.get("fork_turns")
        finite = isinstance(fork, str) and fork in FINITE_HISTORY_TURNS
        if fork != "none" and not finite: errors.append(f"{label}.route.fork_turns must be none or a finite-history string from 1 through 8")
        if not _one(route.get("context_mode"), {"self-contained", "self-contained-finite-history"}): errors.append(f"{label}.route.context_mode is invalid")
        if fork == "none" and route.get("context_mode") != "self-contained": errors.append(f"{label} no-history route requires self-contained context")
        finite_reason = route.get("finite_history_reason")
        concrete_reason = _meaningful_length(finite_reason) >= 8
        if finite and (route.get("context_mode") != "self-contained-finite-history" or not concrete_reason): errors.append(f"{label} finite history requires self-contained-finite-history and a concrete finite_history_reason")
        if not finite and route.get("finite_history_reason") is not None: errors.append(f"{label}.route.finite_history_reason is only allowed for a finite history")
        if not _text(route.get("selection_reason")): errors.append(f"{label}.route.selection_reason must be non-empty")
        route_evidence = _strings(route.get("availability_evidence"), f"{label}.route.availability_evidence", errors, nonempty=True)
        if route_evidence and not set(route_evidence).issubset(set(runtime_evidence)): errors.append(f"{label}.route.availability_evidence must be recorded by runtime")
        role_set = set(roles) if isinstance(roles, list) and all(isinstance(role, str) for role in roles) else set()
        duty_set = set(duties) if isinstance(duties, list) and all(isinstance(duty, str) for duty in duties) else set()
        for role, specialist_label in CRITICAL_SPECIALIST_LABELS.items():
            if role in role_set:
                _require_critical_route(errors, f"{label} {specialist_label}", route)
        if isinstance(model, str) and model in MODEL_DUTIES and duty_set - MODEL_DUTIES[model]: errors.append(f"{label}.route.model lacks capability for its declared duties")
        all_low_assignment = assignment is not None and all(assignment.get(axis) == "low" for axis in ASSESSMENT_FIELDS)
        if model in LUNA_MODELS:
            if effective != "balanced" or duty_set != {"discovery"} or role_set != LUNA_DISCOVERY_ROLES:
                errors.append(f"{label}.route.model only supports bounded repository discovery in Balanced mode")
            if not all_low_assignment:
                errors.append(f"{label}.route.model requires an all-low discovery assignment")
        available_lunas = [candidate for candidate in LUNA_MODELS if candidate in available]
        if effective == "balanced" and all_low_assignment and duty_set == {"discovery"} and available_lunas and model not in LUNA_MODELS:
            warnings.append(f"{label} should prefer {' or '.join(available_lunas)} for bounded all-low discovery when runtime-confirmed; selection_reason should justify the bypass")

    held = plan.get("implementation_hold") is True
    scope = plan.get("execution_scope")
    for name, item in members.items():
        duties = _safe_strings(item.get("duties"))
        paths = _safe_strings(item.get("write_paths"))
        if (held or scope == "read-only") and ({"implementation", "operations"} & set(duties) or paths): errors.append(f"{name} is not allowed to write or operate in held/read-only scope")
        if {"challenge", "review"} & set(duties) and paths: errors.append(f"{name} challenge/review duties must be read-only")
        dependencies = item.get("depends_on", [])
        dependencies = dependencies if isinstance(dependencies, list) else []
        for dependency in dependencies:
            if not isinstance(dependency, str): errors.append(f"{name} has invalid depends_on entry")
            elif dependency not in members: errors.append(f"{name} depends on missing member {dependency}")
            elif dependency == name or _wave(members[dependency].get("wave")) is None or _wave(item.get("wave")) is None or _wave(members[dependency].get("wave")) >= _wave(item.get("wave")):
                errors.append(f"{name} dependency {dependency} must be in an earlier wave")
    active_role_duties = {
        (role, duty) for item in members.values() for role in _safe_strings(item.get("roles")) for duty in _safe_strings(item.get("duties"))
        if role in ROLE_DUTIES and duty in ROLE_DUTIES[role]
    }
    active_roles = {role for role, _ in active_role_duties}
    route_supports_challenge = _critical_route_available(available)
    aggregate_assessment = _aggregate_assessment(assessment, members)
    aggregate_assurance = _requires_high_risk_confirmation(plan.get("task_level"), aggregate_assessment, flags, plan.get("architecture_change"))
    aggregate_semantic_minimum = _semantic_minimum(plan.get("task_level"), aggregate_assessment, flags, plan.get("architecture_change"), gate, plan.get("implementation_hold"))
    critical_requirement_declared = _one(unavailable_requirement, CRITICAL_UNAVAILABLE_REQUIREMENTS)
    unavailable_critical_hold = critical_requirement_declared and held and aggregate_assurance and not route_supports_challenge
    critical_judgments = {requirement for requirements in FLAG_ROLE_DUTY_REQUIREMENTS.values() for requirement in requirements}
    critical_roles = {role for role, _ in critical_judgments}
    if critical_requirement_declared and not unavailable_critical_hold:
        errors.append("runtime.unavailable_requirement is only valid for a held Assurance-critical plan without a safe critical route")
    for flag in flags:
        if flag in FLAG_ROLE_DUTY_REQUIREMENTS:
            if unavailable_critical_hold:
                continue
            for role, duty in FLAG_ROLE_DUTY_REQUIREMENTS[flag]:
                if (role, duty) not in active_role_duties: errors.append(f"risk flag {flag} requires active {role}:{duty}")
            continue
        for choices in RISK_ROLE_REQUIREMENTS.get(flag, []):
            if unavailable_critical_hold and choices <= critical_roles:
                continue
            if not active_roles & choices: errors.append(f"risk flag {flag} requires an active one of {sorted(choices)}")
    challengers = [item for item in members.values() if "challenge" in _safe_strings(item.get("duties"))]
    # A direction hold remains root-owned in Balanced mode.  Child challenge
    # work is mandatory only for actual architecture/critical-risk judgment;
    # route availability must never change ordinary REVISE/STOP team cost.
    risk_needs_challenge = "architecture" in flags or bool(set(flags) & CRITICAL_FLAGS)
    if risk_needs_challenge and route_supports_challenge and not challengers: errors.append("critical risk gate requires challenge evidence on the available safe route")

    builders = [item for item in members.values() if "implementation" in _safe_strings(item.get("duties"))]
    testers = [item for item in members.values() if "test" in _safe_strings(item.get("duties"))]
    reviewers = [item for item in members.values() if "review" in _safe_strings(item.get("duties"))]
    final_reviewers = [item for item in reviewers if "code_reviewer" in _safe_strings(item.get("roles"))]
    for challenger in challengers:
        challenge_duties = set(_safe_strings(challenger.get("duties")))
        if {"design", "implementation"} & challenge_duties or challenger in testers or challenger in final_reviewers:
            errors.append("challenge member must be independent from design, implementation, test, and final review")
    if mode is not None and _one(mode.get("requested"), MODE_REQUESTS) and _one(mode.get("effective"), set(MODE_ORDER)):
        required_mode = "assurance" if aggregate_assurance else aggregate_semantic_minimum
        expected = required_mode if mode["requested"] == "auto" else max((mode["requested"], required_mode), key=MODE_ORDER.get)
        if mode["effective"] != expected: errors.append(f"mode.effective must be {expected} for requested {mode['requested']}")
    if scope == "delivery" and not held:
        _strings(plan.get("acceptance_criteria"), "acceptance_criteria", errors, nonempty=True)
        _strings(plan.get("evidence"), "evidence", errors, nonempty=True)
        if aggregate_assurance and confirmation != "confirmed": errors.append("active critical delivery requires confirmed user evidence")
    # One integration model serves exact role+duty and role-choice risk rules.
    # It rejects disconnected extra specialists as well as missing required
    # ones, so an intermediate Code Reviewer cannot masquerade as final cover.
    covering_finals = [
        reviewer for reviewer in final_reviewers
        if _genuinely_covering_final(reviewer, members, builders, testers, effective)
    ]
    if scope == "delivery" and not held and builders:
        for flag, specialist, specialist_duties in _triggered_specialists(flags, members):
            specialist_name = specialist.get("task_name")
            if not isinstance(specialist_name, str):
                continue
            sequencing = specialist_duties & {"requirements", "planning", "design", "challenge"}
            if sequencing:
                for builder in builders:
                    builder_name = builder.get("task_name")
                    # A mixed design/implementation owner orders its own work
                    # internally; every other builder must consume the design.
                    if builder is specialist:
                        continue
                    if isinstance(builder_name, str) and not _has_path(members, builder_name, specialist_name):
                        errors.append(f"risk flag {flag} specialist {specialist_name} must precede every builder")
            # A mixed implementation specialist is a builder: its delivery is
            # governed by normal final coverage, while any design still has to
            # inform other builders.  Pure verification specialists need the
            # stronger consume-the-complete-chain rule below.
            verification = set() if "implementation" in specialist_duties else specialist_duties & {"test", "review"}
            if verification and specialist not in covering_finals:
                for builder in builders:
                    builder_name = builder.get("task_name")
                    if isinstance(builder_name, str) and builder is not specialist and not _has_path(members, specialist_name, builder_name):
                        errors.append(f"risk flag {flag} verification specialist {specialist_name} must cover every builder")
                if not any(_has_path(members, final["task_name"], specialist_name) for final in covering_finals):
                    errors.append(f"risk flag {flag} verification specialist {specialist_name} must feed a genuinely covering final Code Reviewer")
            if "operations" in specialist_duties and "implementation" not in specialist_duties:
                if not any(_has_path(members, specialist_name, final["task_name"]) for final in covering_finals):
                    errors.append(f"risk flag {flag} operations specialist {specialist_name} must follow a genuinely covering final Code Reviewer")
    if effective == "lean":
        valid_lean = plan.get("task_level") == "L1" and all(aggregate_assessment[axis] == "low" for axis in ASSESSMENT_FIELDS) and not flags and not plan.get("architecture_change") and gate == "GO" and not held
        if not valid_lean: errors.append("Lean requires L1, all-low assessment, GO, and no risks, architecture change, or hold")
        if len(members) > 1: errors.append("Lean permits only the root or one optional read-only review member")
        if builders or any(_safe_strings(item.get("write_paths")) for item in members.values()): errors.append("Lean root owns localized implementation; spawned members must not write")
        if members and (len(reviewers) != 1 or any("review" not in _safe_strings(item.get("duties")) for item in members.values())): errors.append("Lean's optional member must be read-only review")
    if effective == "balanced" and scope == "delivery" and not held:
        if not builders: errors.append("active Balanced delivery requires implementation")
        if not covering_finals: errors.append("Balanced delivery requires one genuinely covering final Code Reviewer")
        if isinstance(plan.get("task_level"), str) and plan.get("task_level") in {"L2", "L3"}:
            for builder in builders:
                if not any(tester is not builder and _has_path(members, tester["task_name"], builder["task_name"]) for tester in testers): errors.append(f"Balanced L2/L3 builder {builder['task_name']} requires independent test coverage")
        for member in members.values():
            duties = _safe_strings(member.get("duties"))
            if "test" in duties and "review" in duties and duties.index("test") > duties.index("review"):
                errors.append("combined test/review duties must be ordered test then review")
    if effective == "assurance":
        for item in members.values():
            roles = set(_safe_strings(item.get("roles")))
            duties = set(_safe_strings(item.get("duties")))
            active_pairs = {(role, duty) for role in roles for duty in duties if role in ROLE_DUTIES and duty in ROLE_DUTIES[role]}
            broad_critical_judgment = bool(ASSURANCE_CRITICAL_ROLES & roles and CRITICAL_JUDGMENT_DUTIES & duties)
            if active_pairs & critical_judgments or broad_critical_judgment:
                route = item.get("route", {}) if isinstance(item.get("route"), dict) else {}
                _require_critical_route(errors, f"Assurance critical judgment {item.get('task_name')}", route)
        if held:
            warnings.append("held Assurance plan is not a completed delivery chain")
        elif scope == "delivery":
            if not challengers or not builders or not testers or not final_reviewers: errors.append("Assurance delivery requires challenge, implementation, test, and final review")
            for builder in builders:
                if builder in testers or builder in reviewers: errors.append("Assurance builder cannot own test or review")
                if not any(_has_path(members, builder["task_name"], challenge["task_name"]) for challenge in challengers): errors.append("Assurance implementation must depend on challenge")
            for challenge in challengers:
                if {"design", "implementation"} & set(_safe_strings(challenge.get("duties"))): errors.append("Assurance challenge author cannot design or implement")
                if challenge in testers or challenge in final_reviewers: errors.append("Assurance challenge must be independent from test and final review")
            for builder in builders:
                if not any(tester is not builder and _has_path(members, tester["task_name"], builder["task_name"]) for tester in testers): errors.append(f"Assurance builder {builder['task_name']} requires independent test coverage")
            if not covering_finals:
                errors.append("Assurance requires one independent final Code Reviewer covering all testers and builders")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--receipt", type=Path, help="validate supplied runtime observations against this plan")
    args = parser.parse_args()
    try:
        plan = load_plan_json(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        print(f"invalid plan file: {exc}", file=sys.stderr)
        return 2
    errors, warnings = validate(plan)
    if args.receipt is not None:
        try:
            receipt = load_plan_json(args.receipt.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError, RecursionError) as exc:
            print(f"invalid receipt file: {exc}", file=sys.stderr)
            return 2
        errors.extend(validate_receipt(plan, receipt))
    for warning in warnings: print(f"warning: {warning}")
    for error in errors: print(f"error: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
