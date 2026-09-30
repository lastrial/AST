#!/usr/bin/env python3
"""Deterministic regression and adversarial tests for schema v3."""
from __future__ import annotations

import copy
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

if __package__:
    from . import validate_team_plan as validator
else:
    import validate_team_plan as validator

EVIDENCE = ["Current runtime capability report"]
AVAILABLE = {
    "gpt-5.6-sol": ["low", "medium", "high", "xhigh", "max", "ultra"],
    "gpt-5.6-terra": ["low", "medium", "high", "xhigh", "max", "ultra"],
    "gpt-5.6-luna": ["low", "medium", "high", "xhigh", "max"],
    "gpt-6-astra": ["low", "medium", "high", "xhigh", "max", "ultra"],
}


def route(model="gpt-5.6-terra", effort="medium", fork_turns="none", **extra):
    result = {"model": model, "effort": effort, "fork_turns": fork_turns, "context_mode": "self-contained", "selection_reason": "Route fits this bounded assignment.", "availability_evidence": EVIDENCE[:]}
    result.update(extra)
    return result


def delegation(access="forbidden", targets=None):
    return {"invoke_ast": False, "spawn_subagents": False, "ast_access": access, "ast_maintenance_targets": targets or []}


def budget(**extra):
    result = {"max_tool_calls": 24, "max_followups": 1, "max_evidence_items": 8, "no_progress_limit": 3}
    result.update(extra)
    return result


def architecture_basis():
    return {"categories": ["component-boundary"], "rationale": "Moves ownership across an explicit component boundary."}


def member(name, roles, duties, wave, *, depends_on=None, write_paths=None, model="gpt-5.6-terra", effort="medium", assessment=None, **route_extra):
    if write_paths is None:
        write_paths = [f"src/{name}.py"] if "implementation" in duties else []
    return {"task_name": name, "roles": roles, "duties": duties, "wave": wave, "reason": f"{roles[0]} owns a distinct outcome.", "owns": [f"{name} scope"], "write_paths": write_paths, "deliverable": f"{name} evidence", "depends_on": depends_on or [], "assignment_assessment": assessment or {"complexity": "low", "risk": "low", "uncertainty": "low"}, "delegation": delegation(), "execution_budget": budget(), "route": route(model, effort, **route_extra)}


def plan(mode="balanced", level="L1", members=None, scope="delivery"):
    return {"version": 3, "task_level": level, "assessment": {"complexity": "low", "risk": "low", "uncertainty": "low"}, "outcome": "Deliver requested behavior safely", "hard_constraints": [], "proposed_method": None, "assumptions": [], "acceptance_criteria": ["Tests pass"], "architecture_change": False, "architecture_basis": None, "direction_gate": "GO", "user_confirmation": "not-required", "confirmation_evidence": None, "implementation_hold": False, "hold_reasons": [], "risk_flags": [], "evidence": ["Fixture evidence"], "mode": {"requested": mode, "effective": mode, "reasons": ["Fixture mode"]}, "runtime": {"available_models": copy.deepcopy(AVAILABLE), "availability_evidence": EVIDENCE[:]}, "execution_scope": scope, "members": members or []}


def l2_two_child_plan():
    return plan("balanced", "L2", [
        member("terra_m_build", ["backend_developer"], ["implementation"], 1),
        member("terra_m_verify", ["qa_engineer", "code_reviewer"], ["test", "review"], 2, depends_on=["terra_m_build"]),
    ])


class TeamPlanV3Tests(unittest.TestCase):
    def result(self, value):
        return validator.validate(value)

    def errors(self, value):
        return self.result(value)[0]

    def warnings(self, value):
        return self.result(value)[1]

    def assert_valid(self, value):
        self.assertEqual([], self.errors(value))

    def assert_invalid(self, value, text):
        self.assertTrue(any(text in error for error in self.errors(value)), self.errors(value))

    def test_lean_root_only_delivery_and_optional_review(self):
        self.assert_valid(plan("lean"))
        self.assert_valid(plan("lean", members=[member("terra_m_review", ["code_reviewer"], ["review"], 1)]))

    def test_lean_rejects_child_write_risk_and_non_l1(self):
        self.assert_invalid(plan("lean", members=[member("terra_m_build", ["backend_developer"], ["implementation"], 1)]), "Lean root owns")
        value = plan("lean"); value["risk_flags"] = ["security"]
        self.assert_invalid(value, "Lean requires")
        self.assert_invalid(plan("lean", "L2"), "Lean requires")

    def test_balanced_two_child_merge_and_empty_delivery(self):
        self.assert_valid(l2_two_child_plan())
        self.assert_invalid(plan("balanced"), "active Balanced delivery requires implementation")
        value = l2_two_child_plan(); value["members"][1]["duties"] = ["review", "test"]
        self.assert_invalid(value, "ordered test then review")

    def test_balanced_partitioned_builders_are_covered(self):
        value = plan("balanced", "L2", [
            member("terra_m_left", ["backend_developer"], ["implementation"], 1, write_paths=["src/left.py"]),
            member("terra_m_right", ["backend_developer"], ["implementation"], 1, write_paths=["src/right.py"]),
            member("terra_m_left_test", ["qa_engineer"], ["test"], 2, depends_on=["terra_m_left"]),
            member("terra_m_right_test", ["qa_engineer"], ["test"], 2, depends_on=["terra_m_right"]),
            member("terra_m_final", ["code_reviewer"], ["review"], 3, depends_on=["terra_m_left_test", "terra_m_right_test"]),
        ])
        self.assert_valid(value)
        value["members"] = [item for item in value["members"] if item["task_name"] != "terra_m_right_test"]
        self.assert_invalid(value, "terra_m_right requires independent test coverage")

    def test_read_only_scope_and_hold_forbid_all_writes(self):
        self.assert_valid(plan("balanced", scope="read-only"))
        value = l2_two_child_plan(); value["execution_scope"] = "read-only"
        self.assert_invalid(value, "held/read-only")
        value = l2_two_child_plan(); value["implementation_hold"] = True; value["hold_reasons"] = ["Need evidence"]
        self.assert_invalid(value, "held/read-only")

    def test_direction_confirmation_state_machine(self):
        challenge = member("sol_xh_challenge", ["devils_advocate"], ["challenge"], 1, model="gpt-5.6-sol", effort="xhigh")
        value = plan("balanced", members=[challenge]); value.update({"direction_gate": "STOP", "user_confirmation": "pending", "implementation_hold": True, "hold_reasons": ["Unsafe direction"]})
        value["mode"]["effective"] = "balanced"
        self.assert_valid(value)
        value["user_confirmation"] = "confirmed"; value["confirmation_evidence"] = ["User accepted"]
        self.assert_invalid(value, "STOP must be pending")
        value = plan("balanced", members=[challenge]); value.update({"direction_gate": "REVISE", "user_confirmation": "pending", "implementation_hold": True, "hold_reasons": ["Await revision"]})
        self.assert_valid(value)
        value = l2_two_child_plan(); value["members"].insert(0, member("sol_xh_challenge", ["devils_advocate"], ["challenge"], 1, model="gpt-5.6-sol", effort="xhigh")); value["members"][1]["wave"] = 2; value["members"][1]["depends_on"] = ["sol_xh_challenge"]; value["members"][2]["wave"] = 3
        value.update({"direction_gate": "REVISE", "user_confirmation": "confirmed", "confirmation_evidence": ["Revised direction accepted"], "implementation_hold": False, "hold_reasons": []})
        self.assert_valid(value)
        value = plan("balanced"); value["user_confirmation"] = "pending"
        self.assert_invalid(value, "GO cannot")
        value = plan("balanced", scope="read-only"); value["user_confirmation"] = "confirmed"; value["confirmation_evidence"] = ["User confirmed"]
        self.assert_valid(value)
        value = plan("balanced"); value["confirmation_evidence"] = ["unexpected"]
        self.assert_invalid(value, "must be null")

    def test_auto_direction_hold_escalates_to_balanced(self):
        challenge = member("sol_xh_challenge", ["devils_advocate"], ["challenge"], 1, model="gpt-5.6-sol", effort="xhigh")
        for gate in ("STOP", "REVISE"):
            value = plan("auto", members=[challenge]); value["mode"]["effective"] = "balanced"
            value.update({"direction_gate": gate, "user_confirmation": "pending", "implementation_hold": True, "hold_reasons": ["Direction hold"]})
            self.assert_valid(value)
            value["mode"]["effective"] = "lean"
            self.assert_invalid(value, "must be balanced")

    def test_critical_active_delivery_needs_confirmation_and_held_assurance_warns(self):
        value = self.assurance(); value["user_confirmation"] = "not-required"
        self.assert_invalid(value, "active critical delivery")
        value = self.assurance(); value["implementation_hold"] = True; value["hold_reasons"] = ["Await user decision"]
        value["members"] = [item for item in value["members"] if item["task_name"] in {"sol_xh_challenge", "sol_xh_security"}]
        next(item for item in value["members"] if item["task_name"] == "sol_xh_security")["depends_on"] = []
        errors, warnings = self.result(value)
        self.assertEqual([], errors); self.assertIn("held Assurance plan is not a completed delivery chain", warnings)

    def test_all_semantic_high_risk_delivery_requires_confirmation(self):
        value = self.assurance(); value["task_level"] = "L2"; value["risk_flags"] = []; value["user_confirmation"] = "not-required"; value["confirmation_evidence"] = None
        self.assert_invalid(value, "active critical delivery")
        value["user_confirmation"] = "confirmed"; value["confirmation_evidence"] = ["Risk accepted"]
        self.assert_valid(value)
        for flag in ("data-migration", "distributed-consistency"):
            value = self.assurance(); value["user_confirmation"] = "not-required"; value["confirmation_evidence"] = None; value["risk_flags"] = [flag]
            self.assert_invalid(value, "active critical delivery")

    def assurance(self):
        value = plan("assurance", "L4", [
            member("sol_xh_challenge", ["devils_advocate"], ["challenge"], 1, model="gpt-5.6-sol", effort="xhigh"),
            member("terra_m_build", ["backend_developer"], ["implementation"], 2, depends_on=["sol_xh_challenge"]),
            member("terra_m_test", ["qa_engineer"], ["test"], 3, depends_on=["terra_m_build"]),
            member("sol_xh_security", ["security_reviewer"], ["review"], 3, depends_on=["terra_m_build"], model="gpt-5.6-sol", effort="xhigh"),
            member("sol_xh_final", ["code_reviewer"], ["review"], 4, depends_on=["terra_m_test", "sol_xh_security"], model="gpt-5.6-sol", effort="xhigh"),
        ])
        value["assessment"]["risk"] = "high"; value["risk_flags"] = ["security-boundary"]
        value["user_confirmation"] = "confirmed"; value["confirmation_evidence"] = ["User approved boundary change"]
        return value

    def test_assurance_distinct_owners_and_missing_chain(self):
        self.assert_valid(self.assurance())
        for name in ("sol_xh_challenge", "terra_m_build", "terra_m_test", "sol_xh_final"):
            value = self.assurance(); value["members"] = [item for item in value["members"] if item["task_name"] != name]
            self.assert_invalid(value, "Assurance")

    def test_assurance_multi_builder_partition_coverage(self):
        self.assert_valid(self.assurance_multi())
        value = self.assurance_multi(); value["members"] = [item for item in value["members"] if item["task_name"] != "terra_m_right_test"]
        value["members"][-1]["depends_on"] = ["terra_m_left_test"]
        self.assert_invalid(value, "terra_m_right requires independent test coverage")
        value = self.assurance_multi(); value["members"][-1]["depends_on"] = ["terra_m_left_test"]
        self.assert_invalid(value, "covering all testers and builders")

    def assurance_multi(self):
        value = plan("assurance", "L4", [
            member("sol_xh_challenge", ["devils_advocate"], ["challenge"], 1, model="gpt-5.6-sol", effort="xhigh"),
            member("terra_m_left", ["backend_developer"], ["implementation"], 2, depends_on=["sol_xh_challenge"], write_paths=["src/left.py"]),
            member("terra_m_right", ["backend_developer"], ["implementation"], 2, depends_on=["sol_xh_challenge"], write_paths=["src/right.py"]),
            member("terra_m_left_test", ["qa_engineer"], ["test"], 3, depends_on=["terra_m_left"]),
            member("terra_m_right_test", ["qa_engineer"], ["test"], 3, depends_on=["terra_m_right"]),
            member("sol_xh_security", ["security_reviewer"], ["review"], 3, depends_on=["terra_m_left", "terra_m_right"], model="gpt-5.6-sol", effort="xhigh"),
            member("sol_xh_final", ["code_reviewer"], ["review"], 4, depends_on=["terra_m_left_test", "terra_m_right_test", "sol_xh_security"], model="gpt-5.6-sol", effort="xhigh"),
        ])
        value["assessment"]["risk"] = "high"; value["risk_flags"] = ["security-boundary"]
        value["user_confirmation"] = "confirmed"; value["confirmation_evidence"] = ["User approved boundary change"]
        return value

    def test_modes_are_exact_maximum_of_request_and_semantics(self):
        value = plan("auto"); value["mode"]["effective"] = "balanced"
        self.assert_invalid(value, "must be lean")
        value = plan("assurance"); value["mode"]["effective"] = "lean"
        self.assert_invalid(value, "must be assurance")
        value = l2_two_child_plan(); value["mode"]["requested"] = "lean"; value["mode"]["effective"] = "balanced"
        self.assert_valid(value)
        value = l2_two_child_plan(); value["mode"]["requested"] = "balanced"; value["mode"]["effective"] = "assurance"
        self.assert_invalid(value, "must be balanced")

    def test_routes_prefixes_and_forks(self):
        self.assert_valid(plan("balanced", scope="read-only", members=[member("luna_l_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-luna", effort="low")]))
        for effort, code in validator.EFFORT_CODES.items():
            self.assert_valid(plan("balanced", scope="read-only", members=[member(f"sol_{code}_review", ["code_reviewer"], ["review"], 1, model="gpt-5.6-sol", effort=effort)]))
            self.assert_valid(plan("balanced", scope="read-only", members=[member(f"astra_{code}_review", ["code_reviewer"], ["review"], 1, model="gpt-6-astra", effort=effort)]))
        value = plan("balanced", scope="read-only", members=[member("terra_m_read", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-luna", effort="low")])
        self.assert_invalid(value, "must start with luna_l_")
        value = plan("balanced", scope="read-only", members=[member("Terra_m_read", ["repository_analyst"], ["discovery"], 1)])
        self.assert_invalid(value, "lowercase")
        value = plan("balanced", scope="read-only", members=[member("terra_m_read", ["repository_analyst"], ["discovery"], 1)])
        value["members"][0]["route"]["effort"] = "minimal"; self.assert_invalid(value, "six explicit")
        del value["members"][0]["route"]["effort"]; self.assert_invalid(value, "route.effort is required")
        for fork in (2, "all", "default"):
            value = plan("balanced", scope="read-only", members=[member("terra_m_read", ["repository_analyst"], ["discovery"], 1, fork_turns=fork)])
            self.assert_invalid(value, "fork_turns")
        value = plan("balanced", scope="read-only", members=[member("terra_m_read", ["repository_analyst"], ["discovery"], 1, fork_turns="2")])
        self.assert_invalid(value, "finite history requires")
        value["members"][0]["route"].update({"context_mode": "self-contained-finite-history", "finite_history_reason": "One decision is needed."})
        self.assert_valid(value)
        value = plan("balanced", scope="read-only", members=[member("luna_uh_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-luna", effort="ultra")])
        self.assert_invalid(value, "effort is not confirmed")
        value = plan("balanced", scope="read-only", members=[member("terra_m_read", ["repository_analyst"], ["discovery"], 1, **{"context_mode": "self-contained-finite-history"})])
        self.assert_invalid(value, "no-history route requires")
        for invalid_fork in ("01", "+1", "1.0", "9", "9" * 5000):
            value = plan("balanced", scope="read-only", members=[member("terra_m_read", ["repository_analyst"], ["discovery"], 1, fork_turns=invalid_fork, context_mode="self-contained-finite-history", finite_history_reason="Sufficient reason")])
            self.assert_invalid(value, "from 1 through 8")
        value = plan("balanced", scope="read-only", members=[member("terra_m_read", ["repository_analyst"], ["discovery"], 1, fork_turns="2", context_mode="self-contained-finite-history", finite_history_reason="x")])
        self.assert_invalid(value, "concrete finite_history_reason")
        value = plan("balanced", scope="read-only", members=[member("terra_m_read", ["repository_analyst"], ["discovery"], 1, fork_turns="2", context_mode="self-contained-finite-history", finite_history_reason="a      b")])
        self.assert_invalid(value, "concrete finite_history_reason")

    def test_astra_supports_ordinary_and_assurance_critical_work(self):
        ordinary = plan("balanced", "L1", [
            member("astra_m_build", ["backend_developer"], ["implementation"], 1, model="gpt-6-astra", effort="medium"),
            member("astra_m_final", ["code_reviewer"], ["review"], 2, depends_on=["astra_m_build"], model="gpt-6-astra", effort="medium"),
        ])
        self.assert_valid(ordinary)
        self.assert_valid(plan("balanced", scope="read-only", members=[member("sol_m_review", ["code_reviewer"], ["review"], 1, model="gpt-5.6-sol", effort="medium")]))

        value = self.assurance()
        renamed = {}
        for item in value["members"]:
            if item["route"]["model"] == "gpt-5.6-sol":
                old_name = item["task_name"]
                new_name = old_name.replace("sol_", "astra_", 1)
                renamed[old_name] = new_name
                item["task_name"] = new_name
                item["route"]["model"] = "gpt-6-astra"
        for item in value["members"]:
            item["depends_on"] = [renamed.get(name, name) for name in item["depends_on"]]
        self.assert_valid(value)

    def test_critical_specialists_require_astra_or_sol_high_plus_outside_assurance(self):
        value = plan("balanced", scope="read-only", members=[member("astra_h_security", ["security_reviewer"], ["review"], 1, model="gpt-6-astra", effort="high")])
        value["risk_flags"] = ["security"]
        self.assert_valid(value)
        value["members"][0]["route"]["effort"] = "medium"
        value["members"][0]["task_name"] = "astra_m_security"
        self.assert_invalid(value, "Security Reviewer requires high or greater effort")
        value["members"][0] = member("terra_h_security", ["security_reviewer"], ["review"], 1, model="gpt-5.6-terra", effort="high")
        self.assert_invalid(value, "Security Reviewer requires Sol or Astra")
        self.assert_valid(plan("balanced", scope="read-only", members=[member("astra_h_challenge", ["devils_advocate"], ["challenge"], 1, model="gpt-6-astra", effort="high")]))

    def test_luna_high_remains_bounded_to_all_low_repository_discovery(self):
        for effort in ("low", "medium", "high", "xhigh", "max"):
            with self.subTest(effort=effort):
                value = plan("balanced", scope="read-only", members=[member(f"luna_{validator.EFFORT_CODES[effort]}_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-luna", effort=effort)])
                self.assert_valid(value)
        value = plan("balanced", scope="read-only", members=[member("luna_h_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-luna", effort="high")])
        value["members"][0]["assignment_assessment"]["uncertainty"] = "medium"
        self.assert_invalid(value, "requires an all-low discovery assignment")
        value = plan("balanced", scope="read-only", members=[member("luna_h_probe", ["repository_analyst", "security_reviewer"], ["discovery"], 1, model="gpt-5.6-luna", effort="high")])
        self.assert_invalid(value, "only supports bounded repository discovery")

    def test_luna_is_rejected_outside_balanced_including_held_read_only(self):
        for mode in ("lean", "assurance"):
            with self.subTest(mode=mode):
                value = plan(mode, scope="read-only", members=[member("luna_h_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-luna", effort="high")])
                self.assert_invalid(value, "only supports bounded repository discovery in Balanced mode")
        value = plan("assurance", scope="read-only", members=[member("luna_h_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-luna", effort="high")])
        value["implementation_hold"] = True; value["hold_reasons"] = ["Read-only plan remains held"]
        self.assert_invalid(value, "only supports bounded repository discovery in Balanced mode")

    def test_astra_availability_and_legacy_hold_alias_are_evidence_bound(self):
        value = plan("balanced", scope="read-only", members=[member("astra_m_review", ["code_reviewer"], ["review"], 1, model="gpt-6-astra", effort="medium")])
        value["runtime"]["available_models"]["gpt-6-astra"] = ["low"]
        self.assert_invalid(value, "effort is not confirmed for gpt-6-astra")

        value = plan("assurance", scope="delivery")
        value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
        value["implementation_hold"] = True; value["hold_reasons"] = ["Legacy declaration cannot hide Astra"]
        del value["runtime"]["available_models"]["gpt-5.6-sol"]
        value["runtime"]["unavailable_requirement"] = "sol-high-plus"
        self.assert_invalid(value, "only valid for a held Assurance-critical plan without a safe critical route")
        self.assert_invalid(value, "solution_architect:design")

    def test_astra_receipts_keep_prefix_and_route_matching_strict(self):
        value = plan("balanced", scope="read-only", members=[member("astra_m_review", ["code_reviewer"], ["review"], 1, model="gpt-6-astra", effort="medium")])
        receipt = {"source": "runtime-observed", "run_id": "run-astra", "members": [{
            "task_name": "astra_m_review", "actual_model": "gpt-6-astra", "actual_effort": "medium",
            "followup_count": 0, "tool_calls": 1, "model_calls": 1, "input_tokens": None,
            "cached_input_tokens": None, "output_tokens": None, "max_context_tokens": None, "credits": None,
        }]}
        self.assertEqual([], validator.validate_receipt(value, receipt))
        receipt["members"][0]["actual_model"] = "gpt-5.6-sol"
        self.assertTrue(any("actual_model must match" in error for error in validator.validate_receipt(value, receipt)))

    def test_critical_route_untrusted_values_are_errors_not_exceptions(self):
        value = self.assurance()
        value["members"][0]["route"]["model"] = []
        self.assert_invalid(value, "Devil's Advocate requires Sol or Astra")
        value = self.assurance()
        value["members"][0]["route"]["effort"] = {"bad": "shape"}
        self.assert_invalid(value, "Devil's Advocate requires high or greater effort")
        for malformed in ([], {"bad": "shape"}):
            with self.subTest(unavailable_requirement=type(malformed).__name__):
                value = self.assurance()
                value["runtime"]["unavailable_requirement"] = malformed
                self.assert_invalid(value, "runtime.unavailable_requirement must be null")

    def test_assurance_public_api_design_keeps_exact_critical_route_gate(self):
        value = plan("assurance", scope="read-only", members=[
            member("terra_m_api", ["api_architect"], ["design"], 1),
            member("astra_h_review", ["code_reviewer"], ["review"], 1, model="gpt-6-astra", effort="high"),
        ])
        value["risk_flags"] = ["public-api"]
        self.assert_invalid(value, "Assurance critical judgment terra_m_api requires Sol or Astra")
        value["members"][0] = member("astra_h_api", ["api_architect"], ["design"], 1, model="gpt-6-astra", effort="high")
        self.assert_valid(value)

    def test_luna_is_preferred_for_safe_balanced_discovery(self):
        discovery = plan("balanced", "L2", scope="read-only", members=[member("terra_l_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-terra", effort="low")])
        self.assert_valid(discovery)
        self.assertTrue(any("prefer gpt-5.6-luna" in warning for warning in self.warnings(discovery)))
        discovery["members"][0] = member("luna_l_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-luna", effort="low")
        self.assert_valid(discovery)
        self.assertFalse(any("prefer gpt-5.6-luna" in warning for warning in self.warnings(discovery)))

    def test_efficiency_preference_never_overrides_capability_or_assurance(self):
        value = plan("balanced", "L2", scope="read-only", members=[member("terra_l_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-terra", effort="low")])
        value["runtime"]["available_models"].pop("gpt-5.6-luna")
        self.assert_valid(value)
        self.assertFalse(any("prefer gpt-5.6-luna" in warning for warning in self.warnings(value)))

        value = self.assurance()
        self.assertFalse(any("prefer gpt-5.6-luna" in warning for warning in self.warnings(value)))

    def test_new_sol_ids_share_sol_capability_but_require_exact_runtime_evidence(self):
        self.assertEqual("sol", validator.NATIVE_MODELS["gpt-6.1-sol"])
        self.assertEqual("sol", validator.NATIVE_MODELS["gpt-6-sol"])
        for model in ("gpt-6.1-sol", "gpt-6-sol"):
            with self.subTest(model=model):
                ordinary = plan("balanced", scope="read-only", members=[member("sol_m_review", ["code_reviewer"], ["review"], 1, model=model, effort="medium")])
                ordinary["runtime"]["available_models"][model] = ["medium", "high"]
                self.assert_valid(ordinary)
                critical = plan("balanced", scope="read-only", members=[member("sol_h_security", ["security_reviewer"], ["review"], 1, model=model, effort="high")])
                critical["runtime"]["available_models"][model] = ["medium", "high"]
                critical["risk_flags"] = ["security"]
                self.assert_valid(critical)

                delivery = plan("balanced", "L2", [
                    member("sol_m_build", ["backend_developer"], ["implementation"], 1, model=model, effort="medium"),
                    member("sol_m_verify", ["qa_engineer", "code_reviewer"], ["test", "review"], 2, depends_on=["sol_m_build"], model=model, effort="medium"),
                ])
                delivery["runtime"]["available_models"][model] = ["medium", "xhigh"]
                self.assert_valid(delivery)
                receipt = {"source": "runtime-observed", "run_id": "run-sol-delivery", "members": [
                    {"task_name": item["task_name"], "actual_model": model, "actual_effort": "medium", "followup_count": 0,
                     "tool_calls": 1, "model_calls": 1, "input_tokens": None, "cached_input_tokens": None,
                     "output_tokens": None, "max_context_tokens": None, "credits": None}
                    for item in delivery["members"]
                ]}
                self.assertEqual([], validator.validate_receipt(delivery, receipt))
                other_sol = "gpt-6-sol" if model == "gpt-6.1-sol" else "gpt-6.1-sol"
                receipt["members"][0]["actual_model"] = other_sol
                self.assertTrue(any("actual_model must match" in error for error in validator.validate_receipt(delivery, receipt)))

                assurance = self.assurance()
                for item in assurance["members"]:
                    if item["route"]["model"] == "gpt-5.6-sol":
                        item["route"]["model"] = model
                assurance["runtime"]["available_models"][model] = ["xhigh"]
                self.assert_valid(assurance)

                unavailable = copy.deepcopy(ordinary)
                unavailable["runtime"]["available_models"].pop(model)
                unavailable["runtime"]["available_models"][other_sol] = ["medium"]
                self.assert_invalid(unavailable, "must be runtime-confirmed native model")
                unavailable["runtime"]["available_models"][model] = ["low"]
                self.assert_invalid(unavailable, "effort is not confirmed for " + model)
                unavailable["runtime"]["available_models"][model] = ["medium"]
                unavailable["runtime"]["availability_evidence"] = ["Different runtime evidence"]
                self.assert_invalid(unavailable, "availability_evidence must be recorded by runtime")

    def test_new_sol_safe_route_blocks_both_critical_unavailability_aliases(self):
        for model in ("gpt-6.1-sol", "gpt-6-sol"):
            for requirement in ("critical-high-plus", "sol-high-plus"):
                with self.subTest(model=model, requirement=requirement):
                    value = plan("assurance", scope="delivery")
                    value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
                    value["implementation_hold"] = True; value["hold_reasons"] = ["Await a safe critical route"]
                    for critical_model in validator.CRITICAL_ROUTE_MODELS:
                        value["runtime"]["available_models"].pop(critical_model, None)
                    value["runtime"]["available_models"][model] = ["medium"]
                    value["runtime"]["unavailable_requirement"] = requirement
                    self.assert_valid(value)
                    value["runtime"]["available_models"][model] = ["high"]
                    self.assert_invalid(value, "only valid for a held Assurance-critical plan without a safe critical route")

    def test_both_luna_ids_are_balanced_all_low_discovery_only(self):
        for model in ("gpt-5.6-luna", "gpt-6-luna"):
            with self.subTest(model=model):
                value = plan("balanced", scope="read-only", members=[member("luna_h_inventory", ["repository_analyst"], ["discovery"], 1, model=model, effort="high")])
                if model == "gpt-6-luna":
                    value["runtime"]["available_models"][model] = ["low", "medium", "high", "xhigh", "max"]
                self.assert_valid(value)
                for axis in ("complexity", "risk", "uncertainty"):
                    for level in ("medium", "high"):
                        with self.subTest(model=model, axis=axis, level=level):
                            non_low = copy.deepcopy(value)
                            non_low["members"][0]["assignment_assessment"][axis] = level
                            self.assert_invalid(non_low, "requires an all-low discovery assignment")
                outside_balanced = copy.deepcopy(value)
                outside_balanced["mode"] = {"requested": "assurance", "effective": "assurance", "reasons": ["Fixture mode"]}
                self.assert_invalid(outside_balanced, "only supports bounded repository discovery in Balanced mode")

    def test_new_luna_rejects_ultra_in_runtime_and_routes_without_changing_legacy_luna(self):
        legacy = plan("balanced", scope="read-only", members=[member("luna_uh_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-luna", effort="ultra")])
        legacy["runtime"]["available_models"]["gpt-5.6-luna"].append("ultra")
        self.assert_valid(legacy)
        value = plan("balanced", scope="read-only", members=[member("luna_uh_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-6-luna", effort="ultra")])
        value["runtime"]["available_models"]["gpt-6-luna"] = ["low", "ultra"]
        self.assert_invalid(value, "runtime.available_models.gpt-6-luna")
        self.assert_invalid(value, "effort is not supported for gpt-6-luna")

    def test_new_model_ids_remain_exact_and_reject_unadvertised_api_efforts(self):
        value = plan("balanced", scope="read-only", members=[member("sol_h_review", ["code_reviewer"], ["review"], 1, model="gpt-6.2-sol", effort="high")])
        value["runtime"]["available_models"]["gpt-6.2-sol"] = ["high"]
        self.assert_invalid(value, "unsupported native model gpt-6.2-sol")
        self.assert_invalid(value, "must be runtime-confirmed native model")
        for effort in ("none", "minimal"):
            with self.subTest(effort=effort):
                value = plan("balanced", scope="read-only", members=[member("sol_m_review", ["code_reviewer"], ["review"], 1, model="gpt-6-sol", effort=effort)])
                value["runtime"]["available_models"]["gpt-6-sol"] = ["medium"]
                self.assert_invalid(value, "one of the six explicit efforts")
                value["runtime"]["available_models"]["gpt-6-sol"] = [effort]
                self.assert_invalid(value, "runtime.available_models.gpt-6-sol")

    def test_new_generation_receipts_and_luna_preference_keep_family_prefixes_exact(self):
        value = plan("balanced", scope="read-only", members=[member("sol_m_review", ["code_reviewer"], ["review"], 1, model="gpt-6-sol", effort="medium")])
        value["runtime"]["available_models"]["gpt-6-sol"] = ["medium"]
        receipt = {"source": "runtime-observed", "run_id": "run-new-sol", "members": [{
            "task_name": "sol_m_review", "actual_model": "gpt-6.1-sol", "actual_effort": "medium",
            "followup_count": 0, "tool_calls": 1, "model_calls": 1, "input_tokens": None,
            "cached_input_tokens": None, "output_tokens": None, "max_context_tokens": None, "credits": None,
        }]}
        self.assertTrue(any("actual_model must match" in error for error in validator.validate_receipt(value, receipt)))
        receipt["members"][0]["actual_model"] = "gpt-6-astra"
        self.assertTrue(any("actual model/effort prefix" in error for error in validator.validate_receipt(value, receipt)))

        new_only = plan("balanced", "L2", scope="read-only", members=[member("terra_l_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-terra", effort="low")])
        new_only["runtime"]["available_models"].pop("gpt-5.6-luna")
        new_only["runtime"]["available_models"]["gpt-6-luna"] = ["low"]
        self.assertTrue(any("prefer gpt-6-luna" in warning for warning in self.warnings(new_only)))
        new_only["members"][0] = member("luna_l_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-6-luna", effort="low")
        self.assertFalse(any("should prefer" in warning for warning in self.warnings(new_only)))

        mixed = plan("balanced", "L2", scope="read-only", members=[member("terra_l_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-5.6-terra", effort="low")])
        mixed["runtime"]["available_models"]["gpt-6-luna"] = ["low"]
        warning = next(warning for warning in self.warnings(mixed) if "should prefer" in warning)
        self.assertIn("gpt-5.6-luna", warning)
        self.assertIn("gpt-6-luna", warning)
        for selected in ("gpt-5.6-luna", "gpt-6-luna"):
            with self.subTest(selected=selected):
                selected_luna = copy.deepcopy(mixed)
                selected_luna["members"][0] = member("luna_l_inventory", ["repository_analyst"], ["discovery"], 1, model=selected, effort="low")
                self.assert_valid(selected_luna)
                self.assertFalse(any("should prefer" in item for item in self.warnings(selected_luna)))

    def test_new_model_runtime_shapes_never_raise(self):
        for efforts in ([], ["ultra"], ["low", {"unexpected": "shape"}], {"low": True}):
            with self.subTest(efforts=repr(efforts)):
                value = plan("balanced", scope="read-only", members=[member("luna_l_inventory", ["repository_analyst"], ["discovery"], 1, model="gpt-6-luna", effort="low")])
                value["runtime"]["available_models"]["gpt-6-luna"] = efforts
                errors, warnings = self.result(value)
                self.assertTrue(errors)
                self.assertIsInstance(warnings, list)

    def test_paths_role_limits_catalog_and_legacy_unknown(self):
        for unsafe in ("/tmp/a", "src/../a.py", "src\\a.py", "src/*.py", ".", "src/line\nfile.py", "src/\u200bfile.py", "src/\ud800file.py"):
            value = l2_two_child_plan(); value["members"][0]["write_paths"] = [unsafe]
            self.assert_invalid(value, "unsafe or non-normalized")
        value = plan("balanced", "L1", [member("terra_m_a", ["backend_developer"], ["implementation"], 1, write_paths=["src"]), member("terra_m_b", ["backend_developer"], ["implementation"], 1, write_paths=["src/a.py"]), member("terra_m_final", ["code_reviewer"], ["review"], 2, depends_on=["terra_m_a", "terra_m_b"])])
        self.assert_invalid(value, "overlap")
        value = l2_two_child_plan(); value["members"][0]["write_paths"] = ["src/pkg"]
        value["members"][1]["wave"] = 3; value["members"].insert(1, member("terra_m_second", ["backend_developer"], ["implementation"], 2, write_paths=["src/pkg/file.py"]))
        self.assert_invalid(value, "overlaps existing owner")
        value = l2_two_child_plan(); value["members"][0]["write_paths"] = ["src/pkg", "src/pkg/file.py"]
        self.assert_invalid(value, "overlaps existing owner")
        value = l2_two_child_plan(); value["members"][0]["write_paths"] = ["src/Foo.py"]
        value["members"].insert(1, member("terra_m_case", ["backend_developer"], ["implementation"], 2, write_paths=["src/foo.py"]))
        self.assert_invalid(value, "overlaps existing owner")
        value = l2_two_child_plan(); value["members"][0]["write_paths"] = ["src/caf\u00e9.py"]
        value["members"].insert(1, member("terra_m_unicode", ["backend_developer"], ["implementation"], 2, write_paths=["src/cafe\u0301.py"]))
        self.assert_invalid(value, "overlaps existing owner")
        value = plan("balanced", scope="read-only", members=[member("terra_m_manager", ["engineering_manager"], ["planning"], 1)])
        self.assert_invalid(value, "cannot declare engineering_manager")
        value = plan("balanced", scope="read-only", members=[member("terra_m_many", ["repository_analyst", "qa_engineer", "code_reviewer"], ["discovery"], 1)])
        self.assert_invalid(value, "one or two")
        value = plan("balanced", scope="read-only"); value["legacy_route"] = {}
        self.assert_invalid(value, "unknown in schema v3")
        value = plan("balanced", scope="read-only"); value["runtime"]["available_models"]["gpt-5.3-codex-spark"] = ["low"]
        self.assert_invalid(value, "unsupported native model gpt-5.3-codex-spark")
        self.assert_invalid({"version": 1}, "migration required")
        self.assert_invalid({"version": 2}, "migration required")
        catalog = Path(__file__).resolve().parents[1] / "references" / "role-catalog.md"
        self.assertEqual(set(validator.ROLE_DUTIES), validator.load_catalog_ids(catalog))
        self.assertEqual(validator.ROLE_DUTIES, validator.load_catalog_duties(catalog))

    def test_role_duty_self_review_and_risk_activation(self):
        value = plan("balanced", scope="read-only", members=[member("terra_m_bad", ["backend_developer"], ["review"], 1)])
        self.assert_invalid(value, "does not match")
        value = plan("balanced", members=[member("terra_m_self", ["backend_developer", "code_reviewer"], ["implementation", "review"], 1)])
        self.assert_invalid(value, "must be read-only")
        value = plan("assurance", "L3", scope="read-only")
        value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
        self.assert_invalid(value, "solution_architect")

    def test_inert_secondary_risk_roles_do_not_activate(self):
        value = plan("balanced", scope="read-only", members=[member("sol_xh_probe", ["repository_analyst", "security_reviewer"], ["discovery"], 1, model="gpt-5.6-sol", effort="xhigh")])
        value["risk_flags"] = ["security"]
        self.assert_invalid(value, "security_reviewer has no active")
        self.assert_invalid(value, "requires an active")
        value = plan("assurance", scope="read-only", members=[member("sol_xh_probe", ["repository_analyst", "devils_advocate"], ["discovery"], 1, model="gpt-5.6-sol", effort="xhigh")])
        value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
        self.assert_invalid(value, "devils_advocate has no active")
        value = plan("assurance", scope="read-only", members=[member("terra_m_probe", ["repository_analyst", "solution_architect"], ["discovery"], 1)])
        value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
        self.assert_invalid(value, "solution_architect has no active")

    def test_critical_flags_require_specific_role_duties(self):
        value = plan("assurance", scope="read-only", members=[member("sol_xh_arch", ["solution_architect", "devils_advocate"], ["integration", "challenge"], 1, model="gpt-5.6-sol", effort="xhigh")])
        value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
        self.assert_invalid(value, "solution_architect:design")
        value = plan("assurance", scope="read-only", members=[member("sol_xh_security", ["security_reviewer", "devils_advocate"], ["review", "challenge"], 1, model="gpt-5.6-sol", effort="xhigh")])
        value["risk_flags"] = ["security-boundary"]
        self.assert_valid(value)

    def test_delivery_evidence_and_challenge_review_boundaries(self):
        value = l2_two_child_plan(); value["acceptance_criteria"] = []
        self.assert_invalid(value, "acceptance_criteria must be a non-empty")
        value = l2_two_child_plan(); value["evidence"] = []
        self.assert_invalid(value, "evidence must be a non-empty")
        value = plan("balanced", scope="read-only", members=[member("sol_xh_bad", ["devils_advocate", "release_engineer"], ["challenge", "operations"], 1, model="gpt-5.6-sol", effort="xhigh")])
        self.assert_invalid(value, "cannot combine")
        value = plan("balanced", members=[member("terra_m_bad", ["backend_developer", "code_reviewer"], ["implementation", "review"], 1)])
        self.assert_invalid(value, "must be read-only")

    def test_member_high_risk_escalates_effective_mode(self):
        value = l2_two_child_plan(); value["members"][0]["assignment_assessment"]["risk"] = "high"
        self.assert_invalid(value, "must be assurance")
        value = self.assurance(); value["task_level"] = "L2"; value["assessment"]["risk"] = "low"; value["risk_flags"] = []
        value["members"][2]["assignment_assessment"]["risk"] = "high"
        self.assert_valid(value)

    def test_member_axiswise_assessment_blocks_lean(self):
        value = plan("lean", members=[member("terra_m_review", ["code_reviewer"], ["review"], 1, assessment={"complexity": "high", "risk": "low", "uncertainty": "low"})])
        self.assert_invalid(value, "must be balanced")
        self.assert_invalid(value, "Lean requires")

    def test_active_assurance_critical_judgment_requires_critical_route_everywhere(self):
        value = plan("assurance", scope="read-only", members=[
            member("terra_m_arch", ["solution_architect"], ["design"], 1),
            member("sol_xh_challenge", ["devils_advocate"], ["challenge"], 1, model="gpt-5.6-sol", effort="xhigh"),
        ])
        value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
        self.assert_invalid(value, "critical judgment terra_m_arch requires Sol or Astra")

    def test_unavailable_critical_route_hold_is_representable(self):
        value = plan("assurance", scope="delivery")
        value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
        value["implementation_hold"] = True; value["hold_reasons"] = ["Required critical high route is unavailable"]
        del value["runtime"]["available_models"]["gpt-5.6-sol"]
        del value["runtime"]["available_models"]["gpt-6-astra"]
        value["runtime"]["unavailable_requirement"] = "critical-high-plus"
        errors, warnings = self.result(value)
        self.assertEqual([], errors); self.assertIn("held Assurance plan is not a completed delivery chain", warnings)
        value = plan("assurance", scope="delivery")
        value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
        value["implementation_hold"] = True; value["hold_reasons"] = ["Await evidence"]
        self.assert_invalid(value, "solution_architect:design")

    def test_unavailable_declaration_cannot_bypass_balanced_security(self):
        value = plan("balanced", scope="read-only")
        value["risk_flags"] = ["security"]; value["implementation_hold"] = True; value["hold_reasons"] = ["Await safe review"]
        value["runtime"]["available_models"]["gpt-5.6-sol"] = ["medium"]
        self.assert_invalid(value, "requires an active")
        value["runtime"]["unavailable_requirement"] = "sol-high-plus"
        self.assert_invalid(value, "only valid for a held Assurance-critical")

        value = plan("assurance", scope="delivery")
        value["assessment"]["risk"] = "high"; value["risk_flags"] = ["security"]
        value["implementation_hold"] = True; value["hold_reasons"] = ["Required safe route is unavailable"]
        value["runtime"]["available_models"]["gpt-5.6-sol"] = ["medium"]
        value["runtime"]["available_models"]["gpt-6-astra"] = ["medium"]
        value["runtime"]["unavailable_requirement"] = "critical-high-plus"
        errors, warnings = self.result(value)
        self.assertEqual([], errors); self.assertIn("held Assurance plan is not a completed delivery chain", warnings)

    def test_challenge_independence_applies_read_only_and_held(self):
        value = plan("assurance", scope="read-only", members=[member("sol_xh_arch_challenge", ["solution_architect", "devils_advocate"], ["design", "challenge"], 1, model="gpt-5.6-sol", effort="xhigh")])
        value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
        self.assert_invalid(value, "challenge member must be independent")

    def test_strict_json_loader_and_cli_reject_duplicate_nonfinite(self):
        for raw in ('{"version":3,"version":3}', '{"version":NaN}', '{"version":Infinity}', '{"version":-Infinity}', '{"depth":{"number":1e9999}}', '{"depth":{"number":-1e9999}}'):
            with self.assertRaises(ValueError):
                validator.load_plan_json(raw)
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as fixture:
            fixture.write('{"version":3,"version":3}'); fixture.flush()
            previous_argv, stderr = sys.argv, io.StringIO()
            try:
                sys.argv = ["validate_team_plan.py", fixture.name]
                with contextlib.redirect_stderr(stderr):
                    self.assertEqual(2, validator.main())
            finally:
                sys.argv = previous_argv
            self.assertIn("duplicate JSON object key", stderr.getvalue())

    def test_assurance_challenge_cannot_be_final_reviewer(self):
        value = self.assurance()
        value["members"][0]["roles"] = ["devils_advocate", "code_reviewer"]
        value["members"][0]["duties"] = ["challenge", "review"]
        self.assert_invalid(value, "challenge must be independent")

    def test_skill_frontmatter_stays_narrow(self):
        skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
        match = __import__("re").match(r"^---\nname: ai-software-team\ndescription: (.+)\n---", skill)
        self.assertIsNotNone(match)
        description = match.group(1)
        for phrase in ("non-trivial repository", "explicit team request", "explanations", "isolated mechanical edits", "non-software"):
            self.assertIn(phrase, description)
        self.assertIn("After every discovery, challenge, test, or review wave", skill)

    def test_malformed_adversarial_shapes_never_raise(self):
        cases = [
            {"version": 3, "assessment": []},
            {"version": 3, "risk_flags": [{"bad": "shape"}]},
            {"version": 3, "mode": []},
            {"version": 3, "runtime": {"available_models": {"gpt-5.6-sol": [{"x": 1}]}, "availability_evidence": ["e"]}},
            plan("balanced", scope="read-only", members=[{"task_name": [], "roles": [{"bad": 1}], "duties": ["discovery"], "wave": 1, "reason": "x", "owns": ["x"], "write_paths": [], "deliverable": "x", "depends_on": [], "assignment_assessment": [], "route": []}]),
            plan("balanced", scope="read-only", members=[member("terra_m_bad", ["repository_analyst"], [{"nested": "object"}], 1)]),
            plan("balanced", scope="read-only", members=[member("terra_m_bad", ["repository_analyst"], [["nested", "list"]], 1)]),
            plan("balanced", scope="read-only", members=[member("terra_m_bad", [{"nested": "object"}], ["discovery"], 1)]),
        ]
        for case in cases:
            with self.subTest(case=case):
                errors, warnings = self.result(case)
                self.assertTrue(errors)
                self.assertIsInstance(warnings, list)

    def test_every_schema_field_bad_shape_never_raises(self):
        bad_values = [None, 7, [], {}, "__bad__"]
        for field in validator.TOP_FIELDS:
            for bad_value in bad_values:
                value = l2_two_child_plan(); value["version"] = 0; value[field] = copy.deepcopy(bad_value)
                with self.subTest(section="top", field=field, shape=type(bad_value).__name__):
                    errors, _ = self.result(value); self.assertTrue(errors)
        for field in validator.MEMBER_FIELDS:
            for bad_value in bad_values:
                value = l2_two_child_plan(); value["version"] = 0; value["members"][0][field] = copy.deepcopy(bad_value)
                with self.subTest(section="member", field=field, shape=type(bad_value).__name__):
                    errors, _ = self.result(value); self.assertTrue(errors)
        for field in validator.ROUTE_FIELDS:
            for bad_value in bad_values:
                value = l2_two_child_plan(); value["version"] = 0; value["members"][0]["route"][field] = copy.deepcopy(bad_value)
                with self.subTest(section="route", field=field, shape=type(bad_value).__name__):
                    errors, _ = self.result(value); self.assertTrue(errors)

    def test_visible_text_and_concrete_runtime_evidence(self):
        invisible = ("\u200b", "\u2060", "\ufeff", "\u180e", "\u0301\u0308")
        for text in invisible:
            with self.subTest(text=repr(text)):
                value = plan("balanced", scope="read-only"); value["outcome"] = text
                self.assert_invalid(value, "outcome")
                value = plan("balanced", scope="read-only"); value["implementation_hold"] = True; value["hold_reasons"] = [text]
                self.assert_invalid(value, "hold_reasons")
                value = plan("balanced", scope="read-only"); value["user_confirmation"] = "confirmed"; value["confirmation_evidence"] = [text]
                self.assert_invalid(value, "confirmation_evidence")
                value = plan("balanced", scope="read-only"); value["runtime"]["availability_evidence"] = [text]
                self.assert_invalid(value, "runtime.availability_evidence")
                value = plan("balanced", scope="read-only", members=[member("terra_m_read", ["repository_analyst"], ["discovery"], 1, fork_turns="1", context_mode="self-contained-finite-history", finite_history_reason=text)])
                self.assert_invalid(value, "concrete finite_history_reason")
        for evidence in ("runtime availability", "运行时可用能力证据", "🧭 route evidence"):
            value = plan("balanced", scope="read-only"); value["runtime"]["availability_evidence"] = [evidence]
            self.assert_valid(value)
        value = plan("balanced", scope="read-only"); value["runtime"]["availability_evidence"] = ["seven!!"]
        self.assert_invalid(value, "concrete visible evidence")

    def test_critical_specialists_must_be_integrated_before_final_review(self):
        value = self.assurance()
        security = next(item for item in value["members"] if item["task_name"] == "sol_xh_security")
        security["wave"] = 5
        security["depends_on"] = ["terra_m_build"]
        next(item for item in value["members"] if item["task_name"] == "sol_xh_final")["depends_on"] = ["terra_m_test"]
        self.assert_invalid(value, "must feed a genuinely covering final Code Reviewer")

        value = plan("assurance", "L4", [
            member("sol_xh_challenge", ["devils_advocate"], ["challenge"], 1, model="gpt-5.6-sol", effort="xhigh"),
            member("sol_xh_arch", ["solution_architect"], ["design"], 1, model="gpt-5.6-sol", effort="xhigh"),
            member("terra_m_build", ["backend_developer"], ["implementation"], 2, depends_on=["sol_xh_challenge"]),
            member("terra_m_test", ["qa_engineer"], ["test"], 3, depends_on=["terra_m_build"]),
            member("sol_xh_final", ["code_reviewer"], ["review"], 4, depends_on=["terra_m_test"], model="gpt-5.6-sol", effort="xhigh"),
        ])
        value["architecture_change"] = True; value["architecture_basis"] = architecture_basis(); value["risk_flags"] = ["architecture"]
        value["user_confirmation"] = "confirmed"; value["confirmation_evidence"] = ["Architecture accepted"]
        self.assert_invalid(value, "sol_xh_arch must precede every builder")
        arch = next(item for item in value["members"] if item["task_name"] == "sol_xh_arch")
        arch["wave"] = 5; arch["depends_on"] = ["terra_m_build"]
        self.assert_invalid(value, "sol_xh_arch must precede every builder")

        value = self.assurance()
        security = next(item for item in value["members"] if item["task_name"] == "sol_xh_security")
        security["roles"] = ["security_reviewer", "code_reviewer"]
        security["wave"] = 5
        security["depends_on"] = ["terra_m_build"]
        next(item for item in value["members"] if item["task_name"] == "sol_xh_final")["depends_on"] = ["terra_m_test"]
        self.assert_invalid(value, "must feed a genuinely covering final Code Reviewer")

    def test_balanced_compatibility_specialist_precedes_builder(self):
        value = plan("balanced", "L1", [
            member("terra_m_build", ["backend_developer"], ["implementation"], 1),
            member("terra_m_final", ["code_reviewer"], ["review"], 2, depends_on=["terra_m_build"]),
            member("terra_m_arch", ["solution_architect"], ["design"], 3),
        ])
        value["risk_flags"] = ["compatibility"]
        self.assert_invalid(value, "terra_m_arch must precede every builder")
        architect, builder, final = value["members"][2], value["members"][0], value["members"][1]
        architect["wave"] = 1
        builder["wave"] = 2; builder["depends_on"] = ["terra_m_arch"]
        final["wave"] = 3
        self.assert_valid(value)

    def test_risk_specialist_integration_uses_covering_final_semantics(self):
        # An L2 compatibility plan can merge sequential QA and final review;
        # the architect, builder, and merged verifier are the complete team.
        value = plan("balanced", "L2", [
            member("terra_m_arch", ["solution_architect"], ["design"], 1),
            member("terra_m_build", ["backend_developer"], ["implementation"], 2, depends_on=["terra_m_arch"]),
            member("terra_m_verify", ["qa_engineer", "code_reviewer"], ["test", "review"], 3, depends_on=["terra_m_build"]),
        ])
        value["risk_flags"] = ["compatibility"]
        self.assert_valid(value)

        # The security reviewer feeds only a bridge reviewer.  A different
        # final covers build/test but does not consume security evidence.
        value = plan("assurance", "L4", [
            member("sol_xh_challenge", ["devils_advocate"], ["challenge"], 1, model="gpt-5.6-sol", effort="xhigh"),
            member("terra_m_build", ["backend_developer"], ["implementation"], 2, depends_on=["sol_xh_challenge"]),
            member("terra_m_test", ["qa_engineer"], ["test"], 3, depends_on=["terra_m_build"]),
            member("sol_xh_security", ["security_reviewer"], ["review"], 3, depends_on=["terra_m_build"], model="gpt-5.6-sol", effort="xhigh"),
            member("sol_xh_bridge", ["code_reviewer"], ["review"], 4, depends_on=["sol_xh_security"], model="gpt-5.6-sol", effort="xhigh"),
            member("sol_xh_final", ["code_reviewer"], ["review"], 4, depends_on=["terra_m_test"], model="gpt-5.6-sol", effort="xhigh"),
        ])
        value["assessment"]["risk"] = "high"; value["risk_flags"] = ["security"]
        value["user_confirmation"] = "confirmed"; value["confirmation_evidence"] = ["Security risk accepted"]
        self.assert_invalid(value, "sol_xh_security must feed a genuinely covering final")
        next(item for item in value["members"] if item["task_name"] == "sol_xh_final")["depends_on"] = ["terra_m_test", "sol_xh_security"]
        self.assert_valid(value)

    def test_generic_risk_specialists_cannot_follow_final_review(self):
        for flag, specialist in (("security", member("sol_m_security", ["security_reviewer"], ["review"], 3, depends_on=["terra_m_build"], model="gpt-5.6-sol")), ("public-api", member("terra_m_api", ["api_architect"], ["design"], 3))):
            with self.subTest(flag=flag):
                value = plan("balanced", "L1", [
                    member("terra_m_build", ["backend_developer"], ["implementation"], 1),
                    member("terra_m_final", ["code_reviewer"], ["review"], 2, depends_on=["terra_m_build"]),
                    specialist,
                ])
                value["risk_flags"] = [flag]
                self.assert_invalid(value, "specialist")

    def test_operations_only_risk_specialist_follows_covering_final(self):
        value = plan("balanced", "L1", [
            member("terra_m_build", ["backend_developer"], ["implementation"], 1),
            member("terra_m_final", ["code_reviewer"], ["review"], 2, depends_on=["terra_m_build"]),
            member("terra_m_ops", ["devops_engineer"], ["operations"], 3, depends_on=["terra_m_final"]),
        ])
        value["risk_flags"] = ["infrastructure"]
        self.assert_valid(value)
        value["members"][2]["depends_on"] = ["terra_m_build"]
        self.assert_invalid(value, "operations specialist terra_m_ops must follow")

    def test_assurance_generic_security_privacy_specialists_must_feed_final(self):
        for flag in ("security", "privacy"):
            with self.subTest(flag=flag):
                value = self.assurance()
                value["risk_flags"] = [flag]
                security = next(item for item in value["members"] if item["task_name"] == "sol_xh_security")
                security["wave"] = 5; security["depends_on"] = ["terra_m_build"]
                next(item for item in value["members"] if item["task_name"] == "sol_xh_final")["depends_on"] = ["terra_m_test"]
                self.assert_invalid(value, "sol_xh_security must feed a genuinely covering final")

    def test_balanced_direction_hold_is_not_availability_dependent(self):
        results = []
        for efforts in (["medium"], ["high"]):
            value = plan("balanced", scope="read-only")
            value.update({"direction_gate": "REVISE", "user_confirmation": "pending", "implementation_hold": True, "hold_reasons": ["Awaiting direction"]})
            value["runtime"]["available_models"]["gpt-5.6-sol"] = efforts
            errors, _ = self.result(value)
            self.assertEqual([], errors)
            results.append(len(value["members"]))
        self.assertEqual(results[0], results[1])

    def test_architecture_basis_and_child_execution_bounds_are_strict(self):
        value = plan("balanced", scope="read-only")
        value["architecture_basis"] = architecture_basis()
        self.assert_invalid(value, "architecture_basis must be null")
        value = plan("assurance", scope="read-only")
        value["architecture_change"] = True; value["risk_flags"] = ["architecture"]
        self.assert_invalid(value, "architecture_basis must be an object")
        value["architecture_basis"] = {"categories": ["component-boundary", "component-boundary"], "rationale": "short"}
        self.assert_invalid(value, "architecture_basis.categories")
        self.assert_invalid(value, "architecture_basis.rationale")
        value["architecture_basis"] = architecture_basis(); value["architecture_basis"]["unknown"] = True
        self.assert_invalid(value, "architecture_basis.unknown is unknown")
        value = plan("balanced", scope="read-only", members=[member("terra_m_read", ["repository_analyst"], ["discovery"], 1)])
        child = value["members"][0]
        child["delegation"]["spawn_subagents"] = True
        self.assert_invalid(value, "spawn_subagents must be false")
        child["delegation"]["spawn_subagents"] = False; child["delegation"]["invoke_ast"] = True
        self.assert_invalid(value, "invoke_ast must be false")
        child["delegation"] = delegation("explicit-maintenance-targets", ["references/task-routing.md"])
        self.assert_valid(value)
        for invalid_target in ("../SKILL.md", "ai-software-team/SKILL.md", "unrelated/private-plan.md"):
            child["delegation"]["ast_maintenance_targets"] = [invalid_target]
            self.assert_invalid(value, "approved Skill-relative AST artifacts")
        child["delegation"] = delegation("forbidden", ["SKILL.md"])
        self.assert_invalid(value, "forbidden requires empty")
        child["delegation"] = delegation()
        child["delegation"]["unknown"] = True
        self.assert_invalid(value, "delegation.unknown is unknown")
        del child["delegation"]["unknown"]
        child["execution_budget"]["max_tool_calls"] = 65
        self.assert_invalid(value, "from 1 through 64")
        child["execution_budget"] = budget(no_progress_limit=5, max_tool_calls=4)
        self.assert_invalid(value, "no greater than max_tool_calls")
        child["execution_budget"] = budget()
        child["execution_budget"]["unknown"] = 1
        self.assert_invalid(value, "execution_budget.unknown is unknown")

    def test_runtime_receipt_validation_and_cli(self):
        value = l2_two_child_plan()
        receipt = {"source": "runtime-observed", "run_id": "run-123", "members": [
            {"task_name": item["task_name"], "actual_model": item["route"]["model"], "actual_effort": item["route"]["effort"], "followup_count": 1, "tool_calls": 4, "model_calls": 2, "input_tokens": None, "cached_input_tokens": 0, "output_tokens": 3, "max_context_tokens": None, "credits": None}
            for item in value["members"]
        ]}
        self.assertEqual([], validator.validate_receipt(value, receipt))
        receipt["unknown"] = True
        self.assertTrue(any("receipt.unknown is unknown" in error for error in validator.validate_receipt(value, receipt)))
        del receipt["unknown"]
        receipt["members"][0]["unknown"] = True
        self.assertTrue(any("receipt.members[0].unknown is unknown" in error for error in validator.validate_receipt(value, receipt)))
        del receipt["members"][0]["unknown"]
        receipt["members"][0]["actual_model"] = "gpt-5.6-sol"
        self.assertTrue(any("actual_model must match" in error for error in validator.validate_receipt(value, receipt)))
        receipt["members"][0]["actual_model"] = "gpt-5.6-terra"
        receipt["members"][0]["followup_count"] = 2
        self.assertTrue(any("exceeds plan budget" in error for error in validator.validate_receipt(value, receipt)))
        receipt["members"][0]["followup_count"] = 1
        receipt["members"][0]["tool_calls"] = 25
        self.assertTrue(any("tool_calls exceeds plan budget" in error for error in validator.validate_receipt(value, receipt)))
        receipt["members"][0]["tool_calls"] = 1.5
        self.assertTrue(any("tool_calls must be a non-negative integer" in error for error in validator.validate_receipt(value, receipt)))
        receipt["members"][0]["tool_calls"] = 4
        receipt["members"][0]["model_calls"] = 1.5
        self.assertTrue(any("model_calls must be a non-negative integer" in error for error in validator.validate_receipt(value, receipt)))
        receipt["members"][0]["model_calls"] = 2
        receipt["members"][0]["credits"] = -1
        self.assertTrue(any("credits must be" in error for error in validator.validate_receipt(value, receipt)))
        with tempfile.TemporaryDirectory() as directory:
            plan_path, receipt_path = Path(directory) / "plan.json", Path(directory) / "receipt.json"
            plan_path.write_text(__import__("json").dumps(value), encoding="utf-8")
            receipt["members"][0]["credits"] = None
            receipt_path.write_text(__import__("json").dumps(receipt), encoding="utf-8")
            previous_argv = sys.argv
            try:
                sys.argv = ["validate_team_plan.py", str(plan_path), "--receipt", str(receipt_path)]
                self.assertEqual(0, validator.main())
            finally:
                sys.argv = previous_argv

    def test_every_architecture_category_has_a_complete_valid_plan(self):
        for category in validator.ARCHITECTURE_CATEGORIES:
            with self.subTest(category=category):
                value = self.assurance()
                value["architecture_change"] = True
                value["architecture_basis"] = {"categories": [category], "rationale": "Changes an explicitly evidenced architecture boundary."}
                value["risk_flags"].append("architecture")
                value["members"].insert(1, member("sol_xh_arch", ["solution_architect"], ["design"], 1, model="gpt-5.6-sol", effort="xhigh"))
                builder = next(item for item in value["members"] if item["task_name"] == "terra_m_build")
                builder["depends_on"].append("sol_xh_arch")
                self.assert_valid(value)


if __name__ == "__main__":
    unittest.main()
