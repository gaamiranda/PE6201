"""Focused offline tests for the D5 evaluation harness."""

from __future__ import annotations

import json
import io
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from harness import run_eval


def expected(decision: str, **extra: object) -> dict[str, object]:
    return {"case_id": "CLM-TEST", "expected_decision": decision, **extra}



# The summary is committed evidence; these four fields must never carry an absolute path.
PATH_KEYS = (
    "raw_results_path",
    "summary_results_path",
    "judgement_queue_path",
    "judgements_applied_audit_path",
)

class GraderTests(unittest.TestCase):
    def test_matching_decision_passes(self) -> None:
        grade = run_eval.grade_record(
            expected("approve_in_principle"), {"decision": "approve_in_principle"}
        )
        self.assertTrue(grade["passed"])
        self.assertTrue(grade["decision_ok"])

    def test_mismatched_decision_fails(self) -> None:
        grade = run_eval.grade_record(
            expected("approve_in_principle"), {"decision": "escalate"}
        )
        self.assertFalse(grade["passed"])
        self.assertIn("decision mismatch", grade["grading_reason"])

    def test_validator_overridden_fails_even_when_the_decision_matches(self) -> None:
        """A record the loop's evidence validator disowned cannot count as a pass.

        This is the CLM-8910 shape: the decision matches the answer key, so a grader that
        looks only at `decision` scores it green, while the loop has already recorded that
        nothing the agent did supports the record.
        """
        grade = run_eval.grade_record(
            expected("escalate", trigger="policy_lapsed"),
            {
                "decision": "escalate",
                "trigger": "policy_lapsed",
                "validator_overridden": True,
                "validator_gaps": ["an escalation must name exactly one trigger"],
            },
        )
        self.assertFalse(grade["passed"])
        self.assertFalse(grade["code_check_passed"])
        self.assertTrue(grade["decision_ok"])          # stays truthful
        self.assertIn("validator", grade["grading_reason"])

    def test_clean_record_is_unaffected_by_the_validator_check(self) -> None:
        grade = run_eval.grade_record(
            expected("escalate", trigger="policy_lapsed"),
            {"decision": "escalate", "trigger": "policy_lapsed"},
        )
        self.assertTrue(grade["passed"])

    def test_correct_escalation_trigger_passes(self) -> None:
        grade = run_eval.grade_record(
            expected("escalate", trigger="duplicate_claim"),
            {"decision": "escalate", "trigger": "duplicate_claim"},
        )
        self.assertTrue(grade["passed"])
        self.assertTrue(grade["trigger_ok"])

    def test_wrong_escalation_trigger_fails(self) -> None:
        grade = run_eval.grade_record(
            expected("escalate", trigger="duplicate_claim"),
            {"decision": "escalate", "trigger": "policy_lapsed"},
        )
        self.assertFalse(grade["passed"])
        self.assertTrue(grade["decision_ok"])
        self.assertFalse(grade["trigger_ok"])

    def test_missing_escalation_trigger_fails_without_crashing(self) -> None:
        grade = run_eval.grade_record(
            expected("escalate", trigger="duplicate_claim"), {"decision": "escalate"}
        )
        self.assertFalse(grade["passed"])
        self.assertIn("missing", grade["grading_reason"])

    def test_contained_requested_document_passes(self) -> None:
        grade = run_eval.grade_record(
            expected("request_document", missing="itemised bill for line 45378"),
            {
                "decision": "request_document",
                "missing": {"item": "itemised_bill", "for_line": "45378"},
            },
        )
        self.assertTrue(grade["passed"])
        self.assertTrue(grade["missing_item_ok"])
        self.assertTrue(grade["missing_line_ok"])

    def test_wrong_requested_document_fails(self) -> None:
        grade = run_eval.grade_record(
            expected("request_document", missing="itemised bill for line 45378"),
            {
                "decision": "request_document",
                "missing": {"item": "discharge summary", "for_line": "45378"},
            },
        )
        self.assertFalse(grade["passed"])
        self.assertFalse(grade["missing_item_ok"])

    def test_wrong_requested_line_fails(self) -> None:
        grade = run_eval.grade_record(
            expected("request_document", missing="itemised bill for line 45378"),
            {
                "decision": "request_document",
                "missing": {"item": "itemised bill", "for_line": "4537"},
            },
        )
        self.assertFalse(grade["passed"])
        self.assertFalse(grade["missing_line_ok"])

    def test_missing_optional_agent_fields_do_not_crash(self) -> None:
        spec = {
            "case_id": "CLM-TEST",
            "trial": 1,
            "classification": "ordinary",
            "negative": False,
            "expected": expected("approve_in_principle"),
        }
        result = run_eval.build_trial_result(
            spec,
            record={"decision": "approve_in_principle"},
            runtime_error=None,
            backend="scripted",
            model="scripted",
            prompt_version="v2",
            commit_id=None,
            run_id="test",
            evaluated_at_utc="2026-09-10T00:00:00Z",
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["turns"], 0)
        self.assertEqual(result["tools_called"], [])

    def test_structured_preauthorisation_matches_documented_head_noun_rule(self) -> None:
        grade = run_eval.grade_record(
            expected(
                "request_document",
                missing="current pre-authorisation for line 29881, valid on 2026-09-09",
            ),
            {
                "decision": "request_document",
                "missing": {"item": "pre-authorization", "for_line": "29881"},
            },
        )
        self.assertTrue(grade["passed"])

    def test_all_seven_frozen_request_labels_accept_structured_equivalents(self) -> None:
        rows = json.loads(run_eval.ANSWER_KEY.read_text(encoding="utf-8"))
        request_rows = [
            row for row in rows if row.get("expected_decision") == "request_document"
        ]
        self.assertEqual(len(request_rows), 7)
        for row in request_rows:
            match = re.search(r"\bfor\s+line\s+([A-Za-z0-9-]+)\b", row["missing"])
            self.assertIsNotNone(match, row["case_id"])
            item = row["missing"].split(" for line ", 1)[0]
            grade = run_eval.grade_record(
                row,
                {
                    "decision": "request_document",
                    "missing": {"item": item, "for_line": match.group(1)},
                },
            )
            self.assertTrue(grade["passed"], f"{row['case_id']}: {grade}")


class DataAndSchedulerTests(unittest.TestCase):
    def test_duplicate_expected_outcome_ids_are_rejected(self) -> None:
        rows = [expected("approve_in_principle"), expected("escalate", trigger="policy_lapsed")]
        with self.assertRaisesRegex(run_eval.HarnessDataError, "duplicate"):
            run_eval.validate_and_index_expected(rows)

    def test_claim_without_expected_outcome_is_rejected(self) -> None:
        rows = [expected("approve_in_principle")]
        with self.assertRaisesRegex(run_eval.HarnessDataError, "without expected"):
            run_eval.validate_and_index_expected(rows, claim_ids=["CLM-TEST", "CLM-MISSING"])

    def test_frozen_shape_expands_to_76_trials(self) -> None:
        rows: list[dict[str, object]] = []
        for number in range(25):
            rows.append(
                {"case_id": f"A-{number}", "expected_decision": "approve_in_principle"}
            )
        for number in range(7):
            rows.append(
                {
                    "case_id": f"R-{number}",
                    "expected_decision": "request_document",
                    "missing": f"itemised bill for line {45000 + number}",
                }
            )
        for number in range(10):
            rows.append(
                {
                    "case_id": f"E-{number}",
                    "expected_decision": "escalate",
                    "trigger": "policy_lapsed",
                }
            )

        index, counts = run_eval.validate_and_index_expected(
            rows,
            claim_ids=[row["case_id"] for row in rows],
            validate_frozen_shape=True,
        )
        schedule = run_eval.expand_trials(index)
        self.assertEqual(counts["ordinary_trials"], 25)
        self.assertEqual(counts["negative_trials"], 51)
        self.assertEqual(len(schedule), 76)

    def test_raw_trials_and_summary_are_written(self) -> None:
        row = {
            "trial_id": "trial-write-test",
            "case_id": "CLM-TEST",
            "trial": 1,
            "negative": False,
            "passed": True,
            "final_pass": True,
            "code_check_pass": True,
            "check_type": "code",
            "judgement_required": False,
            "judgement_check_pass": None,
            "decision_ok": True,
            "backend": "scripted",
            "model": "scripted",
            "prompt_version": "v2",
            "turns": 1,
            "tokens_in": 10,
            "tokens_out": 2,
            "estimated_cost_usd": 0.001,
            "projected_cost_usd": 0.001,
            "actual_spend_usd": 0.0,
            "tokens_estimated": True,
            "cap_fired": None,
            "runtime_error": None,
            "grading_reason": "decision matches",
        }
        counts = {
            "unique_cases": 1,
            "ordinary_cases": 1,
            "negative_cases": 0,
            "request_document_cases": 0,
            "escalate_cases": 0,
        }
        summary = run_eval.summarise_results(
            [row],
            dataset_counts=counts,
            backend="scripted",
            model="scripted",
            model_source="test",
            prompt_version="v2",
            commit_id=None,
            run_id="write-test",
            started_at_utc="2026-09-10T00:00:00Z",
            finished_at_utc="2026-09-10T00:00:01Z",
        )
        with tempfile.TemporaryDirectory() as directory:
            raw_path, summary_path, queue_path, audit_path = run_eval.write_results(
                [row], summary, output_dir=Path(directory)
            )
            self.assertTrue(raw_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(queue_path.exists())
            self.assertTrue(audit_path.exists())
            self.assertEqual(len(raw_path.read_text(encoding="utf-8").splitlines()), 1)
            saved = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["total_trial_count"], 1)
            # The summary is committed evidence, so the paths it records must never be absolute:
            # an absolute path bakes in whoever ran it and makes two identical runs differ.
            # This output_dir is a temp directory outside the repository, so the contract is the
            # bare filename; see test_summary_paths_are_repo_relative for the in-repo case.
            for key in PATH_KEYS:
                with self.subTest(location="outside-repo", key=key):
                    self.assertFalse(Path(saved[key]).is_absolute())
            self.assertEqual(saved["raw_results_path"], raw_path.name)

        # Same summary written INSIDE the repository: the contract there is a repo-relative
        # path, so the committed evidence names the file without naming the machine.
        output_root = run_eval.ROOT / "results" / "evaluations"
        with tempfile.TemporaryDirectory(dir=output_root) as directory:
            _, summary_path, _, _ = run_eval.write_results(
                [row], summary, output_dir=Path(directory)
            )
            saved = json.loads(summary_path.read_text(encoding="utf-8"))
            for key in PATH_KEYS:
                with self.subTest(location="in-repo", key=key):
                    value = saved[key]
                    self.assertFalse(Path(value).is_absolute())
                    self.assertTrue(value.startswith("results/evaluations/"))
                    self.assertNotIn(str(run_eval.ROOT), value)

    def test_runtime_error_is_recorded_and_next_isolated_trial_still_runs(self) -> None:
        import tools

        isolated_directories: list[str] = []

        def fake_run_case(case_id: str, **kwargs: object) -> dict[str, object]:
            isolated_directories.append(tools._RESULTS)
            if case_id == "CLM-FAIL":
                raise RuntimeError("deliberate offline test failure")
            return {
                "decision": "approve_in_principle",
                "usage": {"turns": 1, "tokens_in": 10, "tokens_out": 2,
                          "cost_usd": 0.0, "cap_fired": None, "tools_called": []},
            }

        schedule = [
            {
                "case_id": "CLM-FAIL",
                "trial": 1,
                "classification": "ordinary",
                "negative": False,
                "expected": expected("approve_in_principle"),
            },
            {
                "case_id": "CLM-PASS",
                "trial": 1,
                "classification": "ordinary",
                "negative": False,
                "expected": expected("approve_in_principle"),
            },
        ]
        with redirect_stdout(io.StringIO()):
            results = run_eval.execute_trials(
                schedule,
                backend="scripted",
                model="google/gemini-2.5-flash-lite",
                prompt_version="v2",
                commit_id=None,
                run_id="offline-test",
                run_case_fn=fake_run_case,
            )

        self.assertEqual(len(results), 2)
        self.assertIn("deliberate offline test failure", results[0]["runtime_error"])
        self.assertFalse(results[0]["passed"])
        self.assertIsNone(results[1]["runtime_error"])
        self.assertTrue(results[1]["passed"])
        self.assertEqual(len(set(isolated_directories)), 2)


class JudgementWorkflowTests(unittest.TestCase):
    MODEL = "google/gemini-2.5-flash-lite"

    def make_result(
        self,
        case_id: str,
        *,
        trial: int = 1,
        code_pass: bool = True,
        negative: bool = False,
    ) -> dict[str, object]:
        expected_row = {
            "case_id": case_id,
            "expected_decision": "approve_in_principle",
            "must_record": ["material fact"],
        }
        spec = {
            "case_id": case_id,
            "trial": trial,
            "classification": "negative" if negative else "ordinary",
            "negative": negative,
            "expected": expected_row,
        }
        record = {
            "decision": "approve_in_principle" if code_pass else "escalate",
            "reason": "material fact",
            "tokens_estimated": True,
            "usage": {
                "turns": 1,
                "tokens_in": 10,
                "tokens_out": 2,
                "cost_usd": 0.001,
                "tools_called": [],
            },
        }
        return run_eval.build_trial_result(
            spec,
            record=record,
            runtime_error=None,
            backend="scripted",
            model=self.MODEL,
            prompt_version="v2",
            commit_id=None,
            run_id="test-run",
            evaluated_at_utc="2026-09-12T00:00:00Z",
        )

    @staticmethod
    def saved_for(row: dict[str, object], judgement_pass: bool) -> dict[str, object]:
        return {
            "trial_id": row["trial_id"],
            "backend": row["backend"],
            "model": row["model"],
            "prompt_version": row["prompt_version"],
            "case_id": row["case_id"],
            "trial": row["trial"],
            "judgement_pass": judgement_pass,
            "reviewer_notes": "offline test review",
        }

    def test_all_42_cases_are_code_checked_and_exactly_six_require_judgement(self) -> None:
        expected_by_id, _ = run_eval.load_evaluation_set()
        results = []
        for spec in run_eval.expand_trials(expected_by_id):
            expected_row = spec["expected"]
            record = {
                "decision": expected_row["expected_decision"],
                "trigger": expected_row.get("trigger"),
            }
            results.append(
                run_eval.build_trial_result(
                    spec,
                    record=record,
                    runtime_error=None,
                    backend="scripted",
                    model=self.MODEL,
                    prompt_version="v2",
                    commit_id=None,
                    run_id="shape-test",
                    evaluated_at_utc="2026-09-12T00:00:00Z",
                )
            )
        checked_cases = {
            row["case_id"] for row in results if isinstance(row["code_check_pass"], bool)
        }
        judgement_cases = {
            row["case_id"] for row in results if row["judgement_required"]
        }
        self.assertEqual(len(checked_cases), 42)
        self.assertEqual(judgement_cases, set(run_eval.JUDGEMENT_CASE_IDS))
        self.assertEqual(
            {row["check_type"] for row in results if row["judgement_required"]},
            {"code+judgement"},
        )
        self.assertEqual(
            {row["check_type"] for row in results if not row["judgement_required"]},
            {"code"},
        )
        queue = run_eval.build_judgement_queue(results)
        self.assertEqual(len(queue), 12)
        self.assertEqual({row["case_id"] for row in queue}, set(run_eval.JUDGEMENT_CASE_IDS))

    def test_judgement_queue_exposes_complete_structured_final_record(self) -> None:
        row = self.make_result("CLM-8888", negative=True)
        structured_record = {
            "decision": "request_document",
            "reason": None,
            "missing": {
                "item": "pre-authorisation reference",
                "for_line": "62480",
                "must_be_valid_on": "2026-09-08",
            },
            "lines_resolved": [
                {"code": "47120", "status": "covered"},
                {
                    "code": "31255",
                    "status": "not_covered",
                    "exclusion": "EX-14 cosmetic dermatology",
                },
            ],
            "trigger": "annual_limit_exceeded",
            "escalate_to": "claims_adjuster",
            "approved_total": 2180,
            "refused_total": 300,
        }
        row["record"] = structured_record

        queued = run_eval.build_judgement_queue([row])[0]

        self.assertEqual(queued["structured_final_record"], structured_record)
        for field in (
            "missing",
            "lines_resolved",
            "trigger",
            "escalate_to",
            "approved_total",
            "refused_total",
        ):
            with self.subTest(field=field):
                self.assertEqual(
                    queued["structured_final_record"][field], structured_record[field]
                )

    def test_judgement_queue_does_not_infer_external_or_hidden_facts(self) -> None:
        row = self.make_result("CLM-9041")
        row["record"] = {
            "decision": "approve_in_principle",
            "lines": [{"code": "47120", "status": "covered"}],
        }

        queued = run_eval.build_judgement_queue([row])[0]

        self.assertEqual(
            queued["structured_final_record"],
            {"decision": "approve_in_principle", "lines": [{"code": "47120", "status": "covered"}]},
        )
        self.assertNotIn("POL-3310", json.dumps(queued["structured_final_record"]))
        self.assertNotIn("transcript", queued)
        self.assertNotIn("thought", {key.casefold() for key in queued})
        self.assertIn("complete structured final record", queued["judgement_question"])
        self.assertEqual(queued["judgement_rule"], run_eval.JUDGEMENT_RULE)

    def test_required_judgement_cannot_silently_default_to_pass(self) -> None:
        row = self.make_result("CLM-8842")
        joined = run_eval.apply_human_judgements([row])
        self.assertEqual(joined[0]["judgement_check"], "missing")
        self.assertIsNone(joined[0]["final_pass"])

    def test_code_pass_and_judgement_pass_produces_final_pass(self) -> None:
        row = self.make_result("CLM-8842", code_pass=True)
        joined = run_eval.apply_human_judgements([row], [self.saved_for(row, True)])
        self.assertTrue(joined[0]["final_pass"])

    def test_code_pass_and_judgement_fail_produces_final_fail(self) -> None:
        row = self.make_result("CLM-8842", code_pass=True)
        joined = run_eval.apply_human_judgements([row], [self.saved_for(row, False)])
        self.assertFalse(joined[0]["final_pass"])

    def test_code_fail_and_judgement_pass_still_produces_final_fail(self) -> None:
        row = self.make_result("CLM-8842", code_pass=False)
        joined = run_eval.apply_human_judgements([row], [self.saved_for(row, True)])
        self.assertFalse(joined[0]["final_pass"])

    def test_non_judgement_case_uses_code_result_as_final(self) -> None:
        row = self.make_result("CLM-NORMAL", code_pass=False)
        joined = run_eval.apply_human_judgements([row])
        self.assertEqual(joined[0]["judgement_check"], "not_required")
        self.assertEqual(joined[0]["final_pass"], joined[0]["code_check_pass"])

    def test_missing_judgement_marks_combined_summary_incomplete(self) -> None:
        row = run_eval.apply_human_judgements([self.make_result("CLM-8842")])[0]
        counts = {
            "unique_cases": 1,
            "ordinary_cases": 1,
            "negative_cases": 0,
            "request_document_cases": 0,
            "escalate_cases": 0,
        }
        summary = run_eval.summarise_results(
            [row],
            dataset_counts=counts,
            backend="scripted",
            model=self.MODEL,
            model_source="test",
            prompt_version="v2",
            commit_id=None,
            run_id="summary-test",
            started_at_utc="2026-09-12T00:00:00Z",
            finished_at_utc="2026-09-12T00:00:01Z",
        )
        self.assertFalse(summary["combined_score_complete"])
        self.assertIsNone(summary["final_combined_pass_rate"])
        self.assertEqual(summary["provisional_code_only_pass_rate"], 1.0)

    def test_saved_judgement_must_match_model_case_and_trial(self) -> None:
        row = self.make_result("CLM-8842", trial=1)
        for field, wrong in (
            ("model", "wrong/model"),
            ("case_id", "CLM-8850"),
            ("trial", 2),
        ):
            saved = self.saved_for(row, True)
            saved[field] = wrong
            with self.subTest(field=field):
                with self.assertRaisesRegex(run_eval.HarnessDataError, "identity mismatch"):
                    run_eval.apply_human_judgements([row], [saved])


if __name__ == "__main__":
    unittest.main()
