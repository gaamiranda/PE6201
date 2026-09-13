"""D5 evaluation runner for Problem A.

The default invocation is deterministic, offline, and free::

    python -m harness.run_eval

The harness owns scheduling, isolation, grading, reporting, and result persistence.  It does
not own the agent, prompts, tools, guardrails, fixture data, or answer key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ANSWER_KEY = ROOT / "A2_reference_data" / "expected_outcomes_A.json"
CLAIMS = ROOT / "A2_reference_data" / "data_A" / "claims.json"
DEFAULT_OUTPUT_DIR = ROOT / "results" / "evaluations"
TRANSCRIPT_META = ROOT / "evaluation" / "transcripts.meta.json"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from contracts import MODEL as DEFAULT_MODEL  # noqa: E402


EXPECTED_UNIQUE_CASES = 42
EXPECTED_ORDINARY_CASES = 25
EXPECTED_NEGATIVE_CASES = 17
EXPECTED_REQUEST_CASES = 7
EXPECTED_ESCALATE_CASES = 10
EXPECTED_TOTAL_TRIALS = 76

JUDGEMENT_CASE_IDS = frozenset(
    {
        "CLM-8842",
        "CLM-8850",
        "CLM-8888",
        "CLM-8925",
        "CLM-8952",
        "CLM-9041",
    }
)
JUDGEMENT_QUESTION = (
    "Does the Agent's reason contain the material facts required by this case's "
    "must_record list?"
)

ALLOWED_DECISIONS = {"approve_in_principle", "request_document", "escalate"}


class HarnessDataError(ValueError):
    """The frozen evaluation set is incomplete, ambiguous, or unexpectedly changed."""


def _read_json_list(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HarnessDataError(f"{label} not found: {path}") from error
    except json.JSONDecodeError as error:
        raise HarnessDataError(f"invalid JSON in {label} {path}: {error}") from error

    if not isinstance(value, list):
        raise HarnessDataError(f"{label} must contain a JSON list, not {type(value).__name__}")
    if any(not isinstance(row, dict) for row in value):
        raise HarnessDataError(f"every row in {label} must be a JSON object")
    return value


def validate_and_index_expected(
    rows: Sequence[Mapping[str, Any]],
    *,
    claim_ids: Iterable[str] | None = None,
    validate_frozen_shape: bool = False,
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    """Validate expected outcomes and return an insertion-ordered case-id index.

    ``claim_ids`` closes both sides of the join: a claim without an expected outcome and an
    expected outcome without a claim are both fatal rather than silently shrinking the run.
    """
    missing_id_rows: list[int] = []
    case_ids: list[str] = []
    index: dict[str, dict[str, Any]] = {}

    for row_number, source_row in enumerate(rows, start=1):
        case_id = source_row.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            missing_id_rows.append(row_number)
            continue

        case_id = case_id.strip()
        case_ids.append(case_id)
        if case_id not in index:
            index[case_id] = dict(source_row)

    if missing_id_rows:
        raise HarnessDataError(
            "expected-outcome rows have missing or invalid case_id values at rows "
            + ", ".join(map(str, missing_id_rows))
        )

    duplicates = sorted(case_id for case_id, count in Counter(case_ids).items() if count > 1)
    if duplicates:
        raise HarnessDataError(f"duplicate expected-outcome case IDs: {', '.join(duplicates)}")

    for case_id, row in index.items():
        decision = row.get("expected_decision")
        if decision not in ALLOWED_DECISIONS:
            raise HarnessDataError(
                f"{case_id} has missing or unknown expected_decision {decision!r}"
            )
        if decision == "escalate" and not isinstance(row.get("trigger"), str):
            raise HarnessDataError(f"{case_id} is an escalation but has no expected trigger")
        if decision == "request_document" and not isinstance(row.get("missing"), str):
            raise HarnessDataError(
                f"{case_id} requests a document but has no expected missing-information sentence"
            )

    if claim_ids is not None:
        claim_id_list = list(claim_ids)
        invalid_claim_ids = [value for value in claim_id_list if not isinstance(value, str) or not value]
        if invalid_claim_ids:
            raise HarnessDataError("claims contain a missing or invalid claim_id")
        duplicate_claims = sorted(
            case_id for case_id, count in Counter(claim_id_list).items() if count > 1
        )
        if duplicate_claims:
            raise HarnessDataError(f"duplicate claim IDs: {', '.join(duplicate_claims)}")

        claim_id_set = set(claim_id_list)
        expected_id_set = set(index)
        without_expected = sorted(claim_id_set - expected_id_set)
        without_claim = sorted(expected_id_set - claim_id_set)
        problems: list[str] = []
        if without_expected:
            problems.append("claims without expected outcomes: " + ", ".join(without_expected))
        if without_claim:
            problems.append("expected outcomes without claims: " + ", ".join(without_claim))
        if problems:
            raise HarnessDataError("; ".join(problems))

    decisions = Counter(row["expected_decision"] for row in index.values())
    ordinary = decisions["approve_in_principle"]
    request = decisions["request_document"]
    escalate = decisions["escalate"]
    negative = request + escalate
    counts = {
        "unique_cases": len(index),
        "ordinary_cases": ordinary,
        "negative_cases": negative,
        "request_document_cases": request,
        "escalate_cases": escalate,
        "ordinary_trials": ordinary,
        "negative_trials": negative * 3,
        "total_trials": ordinary + negative * 3,
    }

    if validate_frozen_shape:
        wanted = {
            "unique_cases": EXPECTED_UNIQUE_CASES,
            "ordinary_cases": EXPECTED_ORDINARY_CASES,
            "negative_cases": EXPECTED_NEGATIVE_CASES,
            "request_document_cases": EXPECTED_REQUEST_CASES,
            "escalate_cases": EXPECTED_ESCALATE_CASES,
            "total_trials": EXPECTED_TOTAL_TRIALS,
        }
        differences = [
            f"{name}={counts[name]} (expected {expected})"
            for name, expected in wanted.items()
            if counts[name] != expected
        ]
        if differences:
            raise HarnessDataError(
                "frozen evaluation-set shape changed; stop before running: "
                + "; ".join(differences)
            )

    return index, counts


def load_evaluation_set(
    answer_key_path: Path = ANSWER_KEY,
    claims_path: Path = CLAIMS,
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    expected_rows = _read_json_list(answer_key_path, "answer key")
    claim_rows = _read_json_list(claims_path, "claims file")
    claim_ids = [row.get("claim_id") for row in claim_rows]
    expected_by_id, counts = validate_and_index_expected(
        expected_rows,
        claim_ids=claim_ids,
        validate_frozen_shape=True,
    )
    missing_cases = sorted(JUDGEMENT_CASE_IDS - set(expected_by_id))
    invalid_must_record = sorted(
        case_id
        for case_id in JUDGEMENT_CASE_IDS & set(expected_by_id)
        if not isinstance(expected_by_id[case_id].get("must_record"), list)
        or not expected_by_id[case_id]["must_record"]
        or any(
            not isinstance(item, str) or not item.strip()
            for item in expected_by_id[case_id]["must_record"]
        )
    )
    if missing_cases or invalid_must_record:
        problems = []
        if missing_cases:
            problems.append("missing judgement cases: " + ", ".join(missing_cases))
        if invalid_must_record:
            problems.append(
                "judgement cases with missing/invalid must_record: "
                + ", ".join(invalid_must_record)
            )
        raise HarnessDataError("; ".join(problems))
    return expected_by_id, counts


def expand_trials(expected_by_id: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Expand ordinary cases once and negative cases three times, preserving key order."""
    schedule: list[dict[str, Any]] = []
    for case_id, expected in expected_by_id.items():
        negative = expected.get("expected_decision") != "approve_in_principle"
        for trial_number in range(1, 4 if negative else 2):
            schedule.append(
                {
                    "case_id": case_id,
                    "trial": trial_number,
                    "classification": "negative" if negative else "ordinary",
                    "negative": negative,
                    "expected": dict(expected),
                }
            )
    return schedule


def make_trial_id(
    *, backend: str, model: str, prompt_version: str, case_id: str, trial: int
) -> str:
    """Return a run-independent identifier for joining a saved human review."""
    identity = {
        "backend": backend,
        "case_id": case_id,
        "model": model,
        "prompt_version": prompt_version,
        "trial": trial,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]
    return f"judgement-{digest}"


def _normalised_tokens(value: Any) -> list[str]:
    """Apply only deterministic normalisation supported by the repository vocabulary."""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = text.replace("authorization", "authorisation")
    text = text.replace("itemized", "itemised")
    text = re.sub(r"[_\-\s]+", " ", text)
    return re.findall(r"[a-z0-9]+", text)


def _grade_missing(expected_text: Any, actual_missing: Any) -> tuple[bool, bool, str]:
    """Grade the structured/prose asymmetry documented in ``src/contracts.py``.

    The narrow interpretation of "head noun" is the final alphanumeric token in ``item``.
    This covers the repository's three documented forms: pre-authorisation, bill, and summary.
    The line must be a scalar and match a complete normalised token; dictionaries and substring
    matches are deliberately rejected.
    """
    if not isinstance(expected_text, str) or not expected_text.strip():
        return False, False, "expected missing-information sentence is absent"
    if not isinstance(actual_missing, dict):
        return False, False, "actual missing information is not a structured object"

    item = actual_missing.get("item")
    line = actual_missing.get("for_line")
    if not isinstance(item, str) or not item.strip():
        return False, False, "actual missing.item is absent"
    if isinstance(line, bool) or not isinstance(line, (str, int)) or not str(line).strip():
        return False, False, "actual missing.for_line is absent or is not a scalar line ID"

    expected_tokens = _normalised_tokens(expected_text)
    item_tokens = _normalised_tokens(item)
    line_tokens = _normalised_tokens(line)
    if not item_tokens:
        return False, False, "actual missing.item has no comparable token"
    if len(line_tokens) != 1:
        return False, False, "actual missing.for_line is not one complete line ID"

    head_noun = item_tokens[-1]
    item_ok = head_noun in expected_tokens
    line_ok = line_tokens[0] in expected_tokens

    failures: list[str] = []
    if not item_ok:
        failures.append(
            f"document head noun {head_noun!r} is not contained in expected missing information"
        )
    if not line_ok:
        failures.append(
            f"line {str(line)!r} is not contained as a complete expected token"
        )
    return item_ok, line_ok, "; ".join(failures) if failures else "document item and line match"


def grade_record(
    expected: Mapping[str, Any],
    record: Any,
) -> dict[str, Any]:
    """Return strict code-check results plus a specific, deterministic reason."""
    expected_decision = expected.get("expected_decision")
    if not isinstance(record, dict):
        return {
            "decision_ok": False,
            "trigger_ok": None,
            "missing_item_ok": None,
            "missing_line_ok": None,
            "code_check_passed": False,
            "passed": False,
            "grading_reason": "run_case did not return a decision dictionary",
        }

    actual_decision = record.get("decision")
    if actual_decision is None or actual_decision == "":
        return {
            "decision_ok": False,
            "trigger_ok": None,
            "missing_item_ok": None,
            "missing_line_ok": None,
            "code_check_passed": False,
            "passed": False,
            "grading_reason": "actual decision is missing",
        }
    if actual_decision not in ALLOWED_DECISIONS:
        return {
            "decision_ok": False,
            "trigger_ok": None,
            "missing_item_ok": None,
            "missing_line_ok": None,
            "code_check_passed": False,
            "passed": False,
            "grading_reason": f"actual decision {actual_decision!r} is unknown",
        }

    decision_ok = actual_decision == expected_decision
    if not decision_ok:
        return {
            "decision_ok": False,
            "trigger_ok": None,
            "missing_item_ok": None,
            "missing_line_ok": None,
            "code_check_passed": False,
            "passed": False,
            "grading_reason": (
                f"decision mismatch: expected {expected_decision!r}, got {actual_decision!r}"
            ),
        }

    if expected_decision == "escalate":
        expected_trigger = expected.get("trigger")
        actual_trigger = record.get("trigger")
        trigger_ok = actual_trigger == expected_trigger
        if actual_trigger is None or actual_trigger == "":
            reason = f"escalation trigger is missing; expected {expected_trigger!r}"
        elif not trigger_ok:
            reason = (
                f"trigger mismatch: expected {expected_trigger!r}, got {actual_trigger!r}"
            )
        else:
            reason = "decision and escalation trigger match"
        return {
            "decision_ok": True,
            "trigger_ok": trigger_ok,
            "missing_item_ok": None,
            "missing_line_ok": None,
            "code_check_passed": trigger_ok,
            "passed": trigger_ok,
            "grading_reason": reason,
        }

    if expected_decision == "request_document":
        item_ok, line_ok, reason = _grade_missing(
            expected.get("missing"), record.get("missing")
        )
        passed = item_ok and line_ok
        return {
            "decision_ok": True,
            "trigger_ok": None,
            "missing_item_ok": item_ok,
            "missing_line_ok": line_ok,
            "code_check_passed": passed,
            "passed": passed,
            "grading_reason": reason,
        }

    return {
        "decision_ok": True,
        "trigger_ok": None,
        "missing_item_ok": None,
        "missing_line_ok": None,
        "code_check_passed": True,
        "passed": True,
        "grading_reason": "decision matches",
    }


def _number(value: Any, default: int | float = 0) -> int | float:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def build_trial_result(
    trial_spec: Mapping[str, Any],
    *,
    record: Any,
    runtime_error: str | None,
    backend: str,
    model: str,
    prompt_version: str,
    commit_id: str | None,
    run_id: str,
    evaluated_at_utc: str,
) -> dict[str, Any]:
    """Flatten the contract's useful fields while preserving expected and raw records."""
    expected = trial_spec["expected"]
    safe_record = record if isinstance(record, dict) else {}
    usage = safe_record.get("usage")
    safe_usage = usage if isinstance(usage, dict) else {}

    if runtime_error:
        grade = {
            "decision_ok": False,
            "trigger_ok": None,
            "missing_item_ok": None,
            "missing_line_ok": None,
            "code_check_passed": False,
            "passed": False,
            "grading_reason": f"runtime error: {runtime_error}",
        }
    else:
        grade = grade_record(expected, record)

    trial_number = int(trial_spec["trial"])
    negative = bool(trial_spec["negative"])
    case_id = str(trial_spec["case_id"])
    judgement_required = case_id in JUDGEMENT_CASE_IDS
    code_check_pass = bool(grade["code_check_passed"])
    trial_id = make_trial_id(
        backend=backend,
        model=model,
        prompt_version=prompt_version,
        case_id=case_id,
        trial=trial_number,
    )
    result = {
        "run_id": run_id,
        "trial_id": trial_id,
        "case_id": case_id,
        "trial": trial_number,
        "classification": trial_spec["classification"],
        "negative": negative,
        "backend": backend,
        "model": model,
        "prompt_version": prompt_version,
        "expected_decision": expected.get("expected_decision"),
        "actual_decision": safe_record.get("decision"),
        "expected_trigger": expected.get("trigger"),
        "actual_trigger": safe_record.get("trigger"),
        "expected_missing": expected.get("missing"),
        "actual_missing": safe_record.get("missing"),
        "actual_reason": safe_record.get("reason"),
        "must_record": list(expected.get("must_record", [])),
        "check": "code+judgement" if judgement_required else "code",
        "check_type": "code+judgement" if judgement_required else "code",
        "judgement_required": judgement_required,
        "judgement_check": "missing" if judgement_required else "not_required",
        "judgement_check_pass": None if judgement_required else None,
        "judgement_ok": None,
        "judgement_notes": None,
        "reviewer": None,
        "reviewed_at_utc": None,
        **grade,
        "code_check": "pass" if code_check_pass else "fail",
        "code_check_pass": code_check_pass,
        "final_pass": None if judgement_required else code_check_pass,
        "passed": None if judgement_required else code_check_pass,
        "notes": grade["grading_reason"],
        "turns": _number(safe_usage.get("turns")),
        "tokens_in": _number(safe_usage.get("tokens_in")),
        "tokens_out": _number(safe_usage.get("tokens_out")),
        "estimated_cost_usd": _number(safe_usage.get("cost_usd"), 0.0),
        "projected_cost_usd": _number(safe_usage.get("cost_usd"), 0.0),
        "actual_spend_usd": (
            0.0
            if backend == "scripted"
            else safe_usage.get("actual_spend_usd")
        ),
        "cap_fired": safe_usage.get("cap_fired"),
        "tools_called": (
            list(safe_usage.get("tools_called", []))
            if isinstance(safe_usage.get("tools_called", []), list)
            else []
        ),
        "model_calls": _number(safe_record.get("model_calls")),
        "tokens_estimated": safe_record.get("tokens_estimated"),
        "record_timestamp": safe_record.get("ts"),
        "evaluated_at_utc": evaluated_at_utc,
        "commit_id": commit_id,
        "runtime_error": runtime_error,
        "rerun_status": "scheduled_repeat" if negative and trial_number > 1 else "initial_trial",
        "rerun_reason": (
            "negative cases require three trials"
            if negative and trial_number > 1
            else None
        ),
        "expected": dict(expected),
        "record": record if isinstance(record, dict) else None,
    }
    return result


def build_judgement_queue(
    results: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build the reproducible human-review queue for every required trial."""
    queue: list[dict[str, Any]] = []
    for row in results:
        if not row.get("judgement_required"):
            continue
        queue.append(
            {
                "trial_id": row["trial_id"],
                "backend": row["backend"],
                "model": row["model"],
                "prompt_version": row["prompt_version"],
                "case_id": row["case_id"],
                "trial": row["trial"],
                "judgement_question": JUDGEMENT_QUESTION,
                "agent_reason": row.get("actual_reason"),
                "must_record": list(row.get("must_record") or []),
                "judgement_pass": None,
                "reviewer_notes": None,
                "reviewer": None,
                "reviewed_at_utc": None,
            }
        )
    return queue


def load_judgements(path: Path) -> list[dict[str, Any]]:
    """Load an auditable JSON or JSONL human-judgement file."""
    try:
        if path.suffix.casefold() == ".jsonl":
            rows = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            rows = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HarnessDataError(f"judgement file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise HarnessDataError(f"invalid JSON in judgement file {path}: {error}") from error
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise HarnessDataError("judgement file must contain JSON objects in a list or JSONL")
    return rows


def load_existing_trial_results(
    path: Path,
    schedule: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Load and validate raw trials for an offline judgement-only pass."""
    rows = load_judgements(path)
    expected_keys = {(str(row["case_id"]), int(row["trial"])) for row in schedule}
    actual_keys: list[tuple[str, int]] = []
    required_identity = ("trial_id", "backend", "model", "prompt_version", "case_id", "trial")
    for number, row in enumerate(rows, start=1):
        missing = [field for field in required_identity if row.get(field) is None]
        if missing:
            raise HarnessDataError(
                f"raw trial row {number} is missing identity fields: " + ", ".join(missing)
            )
        try:
            trial_number = int(row["trial"])
        except (TypeError, ValueError) as error:
            raise HarnessDataError(f"raw trial row {number} has invalid trial number") from error
        case_id = str(row["case_id"])
        actual_keys.append((case_id, trial_number))
        expected_trial_id = make_trial_id(
            backend=str(row["backend"]),
            model=str(row["model"]),
            prompt_version=str(row["prompt_version"]),
            case_id=case_id,
            trial=trial_number,
        )
        if row["trial_id"] != expected_trial_id:
            raise HarnessDataError(f"raw trial row {number} has an invalid stable trial_id")

    duplicate_keys = sorted(key for key, count in Counter(actual_keys).items() if count > 1)
    if duplicate_keys:
        raise HarnessDataError(f"duplicate case/trial rows in raw results: {duplicate_keys}")
    actual_key_set = set(actual_keys)
    if actual_key_set != expected_keys:
        missing = sorted(expected_keys - actual_key_set)
        extra = sorted(actual_key_set - expected_keys)
        raise HarnessDataError(
            f"raw results do not match the frozen schedule; missing={missing}; extra={extra}"
        )

    for field in ("backend", "model", "prompt_version"):
        values = {str(row[field]) for row in rows}
        if len(values) != 1:
            raise HarnessDataError(f"raw results contain multiple {field} values: {sorted(values)}")
    return rows


def apply_human_judgements(
    results: Sequence[Mapping[str, Any]],
    saved_judgements: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Join saved decisions by stable ID and compute combined final results.

    Rows with ``judgement_pass: null`` are treated as unfinished queue entries.  A completed
    row must contain a boolean and identity fields matching the trial, so a judgement cannot
    silently attach to a different model, prompt, case, or repetition.
    """
    result_by_id = {str(row["trial_id"]): row for row in results}
    completed: dict[str, Mapping[str, Any]] = {}
    seen: set[str] = set()
    identity_fields = ("backend", "model", "prompt_version", "case_id", "trial")

    for saved in saved_judgements:
        trial_id = saved.get("trial_id")
        if not isinstance(trial_id, str) or not trial_id:
            raise HarnessDataError("a judgement row is missing trial_id")
        if trial_id in seen:
            raise HarnessDataError(f"duplicate human judgement for trial_id {trial_id}")
        seen.add(trial_id)
        target = result_by_id.get(trial_id)
        if target is None:
            raise HarnessDataError(f"human judgement targets unknown trial_id {trial_id}")
        if not target.get("judgement_required"):
            raise HarnessDataError(f"human judgement targets non-judgement trial {trial_id}")
        mismatches = [
            field
            for field in identity_fields
            if saved.get(field) != target.get(field)
        ]
        if mismatches:
            raise HarnessDataError(
                f"human judgement identity mismatch for {trial_id}: " + ", ".join(mismatches)
            )
        judgement_pass = saved.get("judgement_pass")
        if judgement_pass is None:
            continue
        if not isinstance(judgement_pass, bool):
            raise HarnessDataError(
                f"human judgement for {trial_id} must use boolean judgement_pass"
            )
        completed[trial_id] = saved

    joined: list[dict[str, Any]] = []
    for source in results:
        row = dict(source)
        if not row.get("judgement_required"):
            code_pass = bool(row.get("code_check_pass"))
            row.update(
                {
                    "judgement_check": "not_required",
                    "judgement_check_pass": None,
                    "judgement_ok": None,
                    "final_pass": code_pass,
                    "passed": code_pass,
                }
            )
        elif row["trial_id"] not in completed:
            row.update(
                {
                    "judgement_check": "missing",
                    "judgement_check_pass": None,
                    "judgement_ok": None,
                    "final_pass": None,
                    "passed": None,
                }
            )
        else:
            saved = completed[str(row["trial_id"])]
            judgement_pass = bool(saved["judgement_pass"])
            final_pass = bool(row.get("code_check_pass")) and judgement_pass
            row.update(
                {
                    "judgement_check": "pass" if judgement_pass else "fail",
                    "judgement_check_pass": judgement_pass,
                    "judgement_ok": judgement_pass,
                    "judgement_notes": saved.get("reviewer_notes"),
                    "reviewer": saved.get("reviewer"),
                    "reviewed_at_utc": saved.get("reviewed_at_utc"),
                    "final_pass": final_pass,
                    "passed": final_pass,
                }
            )
        joined.append(row)
    return joined


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def get_commit_id(root: Path = ROOT) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def resolve_model(backend: str, requested_model: str | None) -> tuple[str, str]:
    if requested_model:
        return requested_model, "command_line"
    if backend == "scripted" and TRANSCRIPT_META.exists():
        try:
            meta = json.loads(TRANSCRIPT_META.read_text(encoding="utf-8"))
            recorded_model = meta.get("model")
            if isinstance(recorded_model, str) and recorded_model:
                return recorded_model, "scripted_transcript_provenance"
        except (OSError, json.JSONDecodeError):
            pass
    return DEFAULT_MODEL, "repository_default"


def execute_trials(
    schedule: Sequence[Mapping[str, Any]],
    *,
    backend: str,
    model: str,
    prompt_version: str,
    commit_id: str | None,
    run_id: str,
    run_case_fn: Callable[..., Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute every trial with an isolated gated-action directory.

    The scripted path additionally replaces the live seam with an assertion for the duration of
    the run.  This proves that a default run cannot accidentally consult an API key or network.
    """
    import backends
    import loop
    import tools

    runner = run_case_fn or loop.run_case
    original_results = tools._RESULTS
    original_live = backends._openrouter_complete

    def _forbid_openrouter(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError("scripted evaluation attempted to call OpenRouter")

    if backend == "scripted":
        backends._openrouter_complete = _forbid_openrouter

    results: list[dict[str, Any]] = []
    try:
        print_trial_header()
        for ordinal, spec in enumerate(schedule, start=1):
            record: Any = None
            runtime_error: str | None = None
            safe_case = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(spec["case_id"]))
            with tempfile.TemporaryDirectory(
                prefix=f"pe6201-{safe_case}-t{spec['trial']}-"
            ) as isolated_results:
                tools._RESULTS = isolated_results
                try:
                    record = runner(
                        spec["case_id"],
                        prompt_version=prompt_version,
                        model=model,
                        backend=backend,
                    )
                except Exception as error:  # one bad run must not silently shrink the battery
                    runtime_error = f"{type(error).__name__}: {error}"
                finally:
                    tools._RESULTS = original_results

            result = build_trial_result(
                spec,
                record=record,
                runtime_error=runtime_error,
                backend=backend,
                model=model,
                prompt_version=prompt_version,
                commit_id=commit_id,
                run_id=run_id,
                evaluated_at_utc=_utc_now(),
            )
            results.append(result)
            print_trial_row(ordinal, len(schedule), result)
    finally:
        tools._RESULTS = original_results
        backends._openrouter_complete = original_live

    return results


def summarise_results(
    results: Sequence[Mapping[str, Any]],
    *,
    dataset_counts: Mapping[str, int],
    backend: str,
    model: str,
    model_source: str,
    prompt_version: str,
    commit_id: str | None,
    run_id: str,
    started_at_utc: str,
    finished_at_utc: str,
) -> dict[str, Any]:
    total = len(results)
    code_passed = sum(bool(row.get("code_check_pass")) for row in results)
    decision_passed = sum(bool(row.get("decision_ok")) for row in results)
    negative_rows = [row for row in results if row.get("negative")]
    negative_code_passed = sum(bool(row.get("code_check_pass")) for row in negative_rows)
    judgement_rows = [row for row in results if row.get("judgement_required")]
    completed_judgements = [
        row for row in judgement_rows if isinstance(row.get("judgement_check_pass"), bool)
    ]
    missing_judgements = [
        row for row in judgement_rows if not isinstance(row.get("judgement_check_pass"), bool)
    ]
    combined_complete = not missing_judgements
    final_passed = (
        sum(bool(row.get("final_pass")) for row in results) if combined_complete else None
    )
    negative_final_passed = (
        sum(bool(row.get("final_pass")) for row in negative_rows)
        if combined_complete
        else None
    )
    first_result_by_case: dict[str, Mapping[str, Any]] = {}
    for row in results:
        first_result_by_case.setdefault(str(row["case_id"]), row)
    decision_only_cases_passed = sum(
        bool(row.get("decision_ok")) for row in first_result_by_case.values()
    )
    turn_values = [
        float(row["turns"])
        for row in results
        if isinstance(row.get("turns"), (int, float))
        and not isinstance(row.get("turns"), bool)
    ]

    code_failures_by_case: dict[str, list[str]] = defaultdict(list)
    for row in results:
        if not row.get("code_check_pass"):
            reason = str(row.get("grading_reason") or "unspecified failure")
            if reason not in code_failures_by_case[str(row["case_id"])]:
                code_failures_by_case[str(row["case_id"])].append(reason)

    final_failures_by_case: dict[str, list[str]] = defaultdict(list)
    if combined_complete:
        for row in results:
            if not row.get("final_pass"):
                reasons = [str(row.get("grading_reason") or "unspecified code failure")]
                if row.get("judgement_required") and not row.get("judgement_check_pass"):
                    reasons.append(
                        "human judgement failed"
                        + (
                            f": {row['judgement_notes']}"
                            if row.get("judgement_notes")
                            else ""
                        )
                    )
                for reason in reasons:
                    if reason not in final_failures_by_case[str(row["case_id"])]:
                        final_failures_by_case[str(row["case_id"])].append(reason)

    negative_case_ids = sorted({str(row["case_id"]) for row in negative_rows})
    all_trials_passed_by_negative_case = sum(
        all(
            bool(row.get("code_check_pass"))
            for row in negative_rows
            if row["case_id"] == case_id
        )
        for case_id in negative_case_ids
    )

    def rate(numerator: int, denominator: int) -> float:
        return numerator / denominator if denominator else 0.0

    projected_single_pass = float(
        sum(
            _number(row.get("projected_cost_usd", row.get("estimated_cost_usd")), 0.0)
            for row in results
            if int(_number(row.get("trial"), 0)) == 1
        )
    )
    projected_schedule = float(
        sum(
            _number(row.get("projected_cost_usd", row.get("estimated_cost_usd")), 0.0)
            for row in results
        )
    )
    projected_extra_negative = projected_schedule - projected_single_pass
    token_flags = [row.get("tokens_estimated") for row in results]
    if token_flags and all(flag is True for flag in token_flags):
        token_usage_source = "locally_estimated"
    elif token_flags and all(flag is False for flag in token_flags):
        token_usage_source = "provider_reported"
    else:
        token_usage_source = "mixed_or_unknown"
    actual_spend_values = [row.get("actual_spend_usd") for row in results]
    if backend == "scripted":
        actual_spend: float | None = 0.0
        cost_note = (
            "Scripted replay makes no provider call: actual spend is US$0.00. Projected "
            "costs apply the repository price model to estimated token usage and are not "
            "measured API expenditure."
        )
    elif actual_spend_values and all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in actual_spend_values
    ):
        actual_spend = float(sum(actual_spend_values))
        cost_note = "Actual spend is provider-reported; projected cost remains a separate model."
    else:
        actual_spend = None
        cost_note = (
            "Provider-reported actual spend was unavailable. Projected cost must not be "
            "presented as measured API expenditure."
        )

    summary = {
        "run_id": run_id,
        "started_at_utc": started_at_utc,
        "finished_at_utc": finished_at_utc,
        "commit_id": commit_id,
        "backend": backend,
        "model": model,
        "model_source": model_source,
        "prompt_version": prompt_version,
        "unique_case_count": dataset_counts["unique_cases"],
        "ordinary_case_count": dataset_counts["ordinary_cases"],
        "negative_case_count": dataset_counts["negative_cases"],
        "request_document_case_count": dataset_counts["request_document_cases"],
        "escalate_case_count": dataset_counts["escalate_cases"],
        "ordinary_trial_count": sum(not bool(row.get("negative")) for row in results),
        "negative_trial_count": len(negative_rows),
        "total_trial_count": total,
        "code_checked_trial_count": sum(
            isinstance(row.get("code_check_pass"), bool) for row in results
        ),
        "code_checked_case_count": len(
            {str(row["case_id"]) for row in results if isinstance(row.get("code_check_pass"), bool)}
        ),
        "check_type_case_counts": {
            "code": len(
                {str(row["case_id"]) for row in results if row.get("check_type") == "code"}
            ),
            "code+judgement": len(
                {
                    str(row["case_id"])
                    for row in results
                    if row.get("check_type") == "code+judgement"
                }
            ),
        },
        "provisional_code_only_passed_trial_count": code_passed,
        "provisional_code_only_pass_rate": rate(code_passed, total),
        "provisional_code_only_pass_rate_percent": round(rate(code_passed, total) * 100, 2),
        "provisional_negative_code_passed_trial_count": negative_code_passed,
        "provisional_negative_code_pass_rate": rate(negative_code_passed, len(negative_rows)),
        "provisional_negative_code_pass_rate_percent": round(
            rate(negative_code_passed, len(negative_rows)) * 100, 2
        ),
        "combined_score_complete": combined_complete,
        "combined_score_status": "complete" if combined_complete else "incomplete",
        "final_passed_trial_count": final_passed,
        "final_combined_pass_rate": (
            rate(final_passed, total) if final_passed is not None else None
        ),
        "final_combined_pass_rate_percent": (
            round(rate(final_passed, total) * 100, 2) if final_passed is not None else None
        ),
        "final_negative_trials_passed": negative_final_passed,
        "final_negative_pass_rate": (
            rate(negative_final_passed, len(negative_rows))
            if negative_final_passed is not None
            else None
        ),
        "final_negative_pass_rate_percent": (
            round(rate(negative_final_passed, len(negative_rows)) * 100, 2)
            if negative_final_passed is not None
            else None
        ),
        "required_judgement_case_count": len({str(row["case_id"]) for row in judgement_rows}),
        "required_judgement_case_ids": sorted({str(row["case_id"]) for row in judgement_rows}),
        "required_judgement_trial_count": len(judgement_rows),
        "completed_judgement_trial_count": len(completed_judgements),
        "missing_judgement_trial_count": len(missing_judgements),
        "missing_judgement_trial_ids": [str(row["trial_id"]) for row in missing_judgements],
        "negative_cases_all_trials_passed": all_trials_passed_by_negative_case,
        "negative_case_all_trials_pass_rate": rate(
            all_trials_passed_by_negative_case, len(negative_case_ids)
        ),
        "decision_only_passed": decision_passed,
        "decision_only_pass_rate": rate(decision_passed, total),
        "decision_only_pass_rate_percent": round(rate(decision_passed, total) * 100, 2),
        "decision_only_cases_passed": decision_only_cases_passed,
        "decision_only_case_pass_rate": rate(
            decision_only_cases_passed, len(first_result_by_case)
        ),
        "decision_only_case_pass_rate_percent": round(
            rate(decision_only_cases_passed, len(first_result_by_case)) * 100, 2
        ),
        "failed_case_ids": sorted(final_failures_by_case) if combined_complete else None,
        "failure_reasons": (
            dict(sorted(final_failures_by_case.items())) if combined_complete else None
        ),
        "provisional_code_failed_case_ids": sorted(code_failures_by_case),
        "provisional_code_failure_reasons": dict(sorted(code_failures_by_case.items())),
        "total_input_tokens": int(sum(_number(row.get("tokens_in")) for row in results)),
        "total_output_tokens": int(sum(_number(row.get("tokens_out")) for row in results)),
        "tokens_estimated": token_usage_source == "locally_estimated",
        "token_usage_source": token_usage_source,
        "actual_spend_usd": actual_spend,
        "projected_cost_42_case_single_pass_usd": round(projected_single_pass, 6),
        "projected_cost_76_trial_schedule_usd": round(projected_schedule, 6),
        "projected_cost_additional_negative_trials_usd": round(
            projected_extra_negative, 6
        ),
        "cost_reporting_note": cost_note,
        "median_turns": statistics.median(turn_values) if turn_values else None,
        "cap_fired_count": sum(bool(row.get("cap_fired")) for row in results),
        "runtime_error_count": sum(bool(row.get("runtime_error")) for row in results),
        "rate_denominators": {
            "provisional_code_only_and_decision_only": "all scheduled trials",
            "provisional_negative_code_only": "negative trials (three per negative case)",
            "final_combined": "all scheduled trials, only after every required judgement exists",
            "decision_only_case": "one result per unique case (trial 1)",
        },
    }
    return summary


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return cleaned or "unnamed"


def write_results(
    results: Sequence[Mapping[str, Any]],
    summary: dict[str, Any],
    *,
    output_dir: Path,
) -> tuple[Path, Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = "-".join(
        [
            "eval",
            _slug(str(summary["backend"])),
            _slug(str(summary["model"])),
            _slug(str(summary["prompt_version"])),
            _slug(str(summary["run_id"])),
        ]
    )
    raw_path = output_dir / f"{stem}.trials.jsonl"
    summary_path = output_dir / f"{stem}.summary.json"
    queue_path = output_dir / f"{stem}.judgement-queue.jsonl"
    audit_path = output_dir / f"{stem}.judgements-applied.jsonl"
    output_paths = (raw_path, summary_path, queue_path, audit_path)
    if any(path.exists() for path in output_paths):
        raise FileExistsError(
            "refusing to overwrite an existing evaluation run: "
            + ", ".join(str(path) for path in output_paths)
        )

    with raw_path.open("x", encoding="utf-8", newline="\n") as file:
        for row in results:
            file.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")

    queue = build_judgement_queue(results)
    with queue_path.open("x", encoding="utf-8", newline="\n") as file:
        for row in queue:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    with audit_path.open("x", encoding="utf-8", newline="\n") as file:
        for row in results:
            if not isinstance(row.get("judgement_check_pass"), bool):
                continue
            audit_row = {
                "trial_id": row["trial_id"],
                "backend": row["backend"],
                "model": row["model"],
                "prompt_version": row["prompt_version"],
                "case_id": row["case_id"],
                "trial": row["trial"],
                "judgement_pass": row["judgement_check_pass"],
                "reviewer_notes": row.get("judgement_notes"),
                "reviewer": row.get("reviewer"),
                "reviewed_at_utc": row.get("reviewed_at_utc"),
            }
            file.write(json.dumps(audit_row, ensure_ascii=False, sort_keys=True) + "\n")

    summary["raw_results_path"] = str(raw_path.resolve())
    summary["summary_results_path"] = str(summary_path.resolve())
    summary["judgement_queue_path"] = str(queue_path.resolve())
    summary["judgements_applied_audit_path"] = str(audit_path.resolve())
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return tuple(path.resolve() for path in output_paths)


def print_trial_header() -> None:
    print(
        f"{'run':>7}  {'case':<9} {'try':>3} {'kind':<8} "
        f"{'expected':<20} {'actual':<20} {'result':<8} {'turns':>5}  reason"
    )
    print("-" * 122)


def _short(value: Any, width: int) -> str:
    text = "-" if value is None else str(value).replace("\n", " ")
    return text if len(text) <= width else text[: width - 1] + "…"


def print_trial_row(ordinal: int, total: int, row: Mapping[str, Any]) -> None:
    final = row.get("final_pass")
    result_label = "PENDING" if final is None else ("PASS" if final else "FAIL")
    print(
        f"{ordinal:>3}/{total:<3}  "
        f"{_short(row.get('case_id'), 9):<9} "
        f"{int(row.get('trial', 0)):>3} "
        f"{_short(row.get('classification'), 8):<8} "
        f"{_short(row.get('expected_decision'), 20):<20} "
        f"{_short(row.get('actual_decision'), 20):<20} "
        f"{result_label:<8} "
        f"{int(_number(row.get('turns'))):>5}  "
        f"{_short(row.get('grading_reason'), 52)}"
    )


def print_summary(summary: Mapping[str, Any]) -> None:
    print("\nSummary")
    print("-------")
    print(f"Cases: {summary['unique_case_count']} unique; "
          f"{summary['ordinary_case_count']} ordinary; {summary['negative_case_count']} negative "
          f"({summary['request_document_case_count']} request_document, "
          f"{summary['escalate_case_count']} escalate)")
    print(f"Trials: {summary['ordinary_trial_count']} ordinary + "
          f"{summary['negative_trial_count']} negative = {summary['total_trial_count']} total")
    print(f"Code checks: {summary['code_checked_case_count']} cases / "
          f"{summary['code_checked_trial_count']} trials")
    print(f"Provisional code-only rate: "
          f"{summary['provisional_code_only_passed_trial_count']}/"
          f"{summary['total_trial_count']} "
          f"({summary['provisional_code_only_pass_rate_percent']:.2f}%)")
    print(f"Provisional negative code-only rate: "
          f"{summary['provisional_negative_code_passed_trial_count']}/"
          f"{summary['negative_trial_count']} "
          f"({summary['provisional_negative_code_pass_rate_percent']:.2f}%)")
    if summary["combined_score_complete"]:
        print(f"Final combined pass rate: {summary['final_passed_trial_count']}/"
              f"{summary['total_trial_count']} "
              f"({summary['final_combined_pass_rate_percent']:.2f}%)")
        print(f"Final negative pass rate: {summary['final_negative_trials_passed']}/"
              f"{summary['negative_trial_count']} "
              f"({summary['final_negative_pass_rate_percent']:.2f}%)")
    else:
        print("Final combined pass rate: INCOMPLETE — "
              f"{summary['missing_judgement_trial_count']} required human judgements missing")
    print(f"Decision-only sanity rate: {summary['decision_only_passed']}/"
          f"{summary['total_trial_count']} ({summary['decision_only_pass_rate_percent']:.2f}%) "
          "across weighted trials")
    print(f"Decision-only case rate: {summary['decision_only_cases_passed']}/"
          f"{summary['unique_case_count']} "
          f"({summary['decision_only_case_pass_rate_percent']:.2f}%) across unique cases")
    print(f"Tokens: {summary['total_input_tokens']} in; {summary['total_output_tokens']} out")
    actual_spend = summary["actual_spend_usd"]
    print("Actual spend: " + ("unavailable" if actual_spend is None else f"US${actual_spend:.2f}"))
    print(f"Projected cost, 42-case single pass: "
          f"US${summary['projected_cost_42_case_single_pass_usd']:.6f}")
    print(f"Projected cost, formal 76-trial schedule: "
          f"US${summary['projected_cost_76_trial_schedule_usd']:.6f}")
    print("Cost note: " + str(summary["cost_reporting_note"]))
    print(f"Median turns: {summary['median_turns']}; caps fired: "
          f"{summary['cap_fired_count']}; runtime errors: {summary['runtime_error_count']}")
    print("Provisional code-failed case IDs: "
          + (", ".join(summary["provisional_code_failed_case_ids"]) or "none"))
    for case_id, reasons in summary["provisional_code_failure_reasons"].items():
        print(f"  {case_id}: {' | '.join(reasons)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the PE6201 Problem A evaluation battery")
    parser.add_argument(
        "--backend",
        choices=("scripted", "openrouter"),
        default="scripted",
        help="model backend (default: scripted; offline and free)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "model ID; scripted defaults to the model recorded in transcripts.meta.json, "
            "live defaults to contracts.MODEL"
        ),
    )
    parser.add_argument(
        "--prompt-version",
        choices=("v1", "v2"),
        default="v2",
        help="descriptor/prompt version (default: v2)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"directory for JSONL and JSON results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="optional unique output identifier; defaults to a UTC timestamp",
    )
    parser.add_argument(
        "--judgements",
        type=Path,
        default=None,
        help=(
            "saved human judgement JSON/JSONL; use a prior judgement-queue file as a "
            "template and fill judgement_pass/reviewer_notes"
        ),
    )
    parser.add_argument(
        "--input-results",
        type=Path,
        default=None,
        help=(
            "existing raw trials JSONL to combine with --judgements without running a backend"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        expected_by_id, counts = load_evaluation_set()
    except HarnessDataError as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2

    schedule = expand_trials(expected_by_id)
    if len(schedule) != counts["total_trials"]:
        print(
            f"BLOCKED: scheduler produced {len(schedule)} trials, expected {counts['total_trials']}",
            file=sys.stderr,
        )
        return 2

    started_at = _utc_now()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    try:
        if args.input_results:
            if not args.judgements:
                raise HarnessDataError("--input-results requires --judgements")
            results = load_existing_trial_results(args.input_results, schedule)
            backend = str(results[0]["backend"])
            model = str(results[0]["model"])
            prompt_version = str(results[0]["prompt_version"])
            commit_values = {row.get("commit_id") for row in results}
            commit_id = commit_values.pop() if len(commit_values) == 1 else None
            model_source = "loaded_trial_results"
            for row in results:
                row["source_run_id"] = row.get("run_id")
                row["run_id"] = run_id
            print(f"Loaded raw trials: {args.input_results.resolve()}")
            print("Backend execution: skipped (offline judgement-only pass)")
        else:
            backend = args.backend
            model, model_source = resolve_model(backend, args.model)
            prompt_version = args.prompt_version
            commit_id = get_commit_id()
            print(f"Backend: {backend}")
            print(f"Model: {model} ({model_source})")
            print(f"Prompt version: {prompt_version}")
            print(f"Commit: {commit_id or 'unknown'}")
            print(
                f"Validated schedule: {counts['unique_cases']} cases; "
                f"{counts['ordinary_trials']} ordinary trials; "
                f"{counts['negative_trials']} negative trials; {counts['total_trials']} total\n"
            )
            results = execute_trials(
                schedule,
                backend=backend,
                model=model,
                prompt_version=prompt_version,
                commit_id=commit_id,
                run_id=run_id,
            )
        saved_judgements = load_judgements(args.judgements) if args.judgements else []
        results = apply_human_judgements(results, saved_judgements)
    except HarnessDataError as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2
    finished_at = _utc_now()
    summary = summarise_results(
        results,
        dataset_counts=counts,
        backend=backend,
        model=model,
        model_source=model_source,
        prompt_version=prompt_version,
        commit_id=commit_id,
        run_id=run_id,
        started_at_utc=started_at,
        finished_at_utc=finished_at,
    )

    try:
        raw_path, summary_path, queue_path, audit_path = write_results(
            results, summary, output_dir=args.output_dir
        )
    except OSError as error:
        print_summary(summary)
        print(f"ERROR: evaluation finished but results could not be saved: {error}", file=sys.stderr)
        return 1

    print_summary(summary)
    print(f"Raw trial results: {raw_path}")
    print(f"Summary results: {summary_path}")
    print(f"Human judgement queue: {queue_path}")
    print(f"Applied judgement audit: {audit_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
