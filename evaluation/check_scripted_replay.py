"""Run the complete recorded evaluation twice without network access.

This is the Step 4 reproducibility check for D5(a).  It keeps gated-action
writes in temporary directories and saves both runs plus a comparison report
under evaluation/.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
EVALUATION = ROOT / "evaluation"
ANSWER_KEY = ROOT / "A2_reference_data" / "expected_outcomes_A.json"
RUN_1_PATH = EVALUATION / "scripted_run_1.json"
RUN_2_PATH = EVALUATION / "scripted_run_2.json"
REPORT_PATH = EVALUATION / "scripted_replay_check.json"
ORIGINAL_DECISIONS = ROOT / "results" / "decisions.jsonl"
ISOLATED_RESULTS = EVALUATION / "step4_isolated_results"
MODEL_ID = "google/gemini-2.5-flash-lite"

# A scripted check must neither require nor accidentally use a live API key.
os.environ.pop("OPENROUTER_API_KEY", None)
sys.path.insert(0, str(SRC))

import backends  # noqa: E402
import loop  # noqa: E402
import tools  # noqa: E402


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_case_ids() -> list[str]:
    rows = json.loads(ANSWER_KEY.read_text(encoding="utf-8"))
    case_ids = [row["case_id"] for row in rows]
    if len(case_ids) != 42 or len(set(case_ids)) != 42:
        raise RuntimeError(
            f"Expected 42 unique case ids in {ANSWER_KEY}, found {len(case_ids)}"
        )
    return case_ids


def _without_runtime_timestamp(value: Any) -> Any:
    """Remove only run_case's wall-clock field before reproducibility comparison."""
    if isinstance(value, list):
        return [_without_runtime_timestamp(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _without_runtime_timestamp(item)
            for key, item in value.items()
            if key != "ts"
        }
    return value


def _forbid_live_backend(*args: Any, **kwargs: Any) -> dict:
    raise AssertionError("Step 4 attempted to call the live OpenRouter backend")


def _run_once(case_ids: list[str], results_dir: Path) -> tuple[list[dict], dict[str, str]]:
    tools._RESULTS = str(results_dir)
    records: list[dict] = []
    failures: dict[str, str] = {}

    for number, case_id in enumerate(case_ids, start=1):
        print(f"[{number:02d}/42] {case_id}")
        try:
            records.append(
                loop.run_case(
                    case_id,
                    backend="scripted",
                    model=MODEL_ID,
                )
            )
        except Exception as error:  # keep checking the rest of the set
            failures[case_id] = f"{type(error).__name__}: {error}"

    return records, failures


def main() -> None:
    case_ids = _load_case_ids()
    decisions_hash_before = _sha256(ORIGINAL_DECISIONS)

    # This assertion-backed replacement proves that explicit scripted dispatch
    # never crosses the live provider seam.
    backends._openrouter_complete = _forbid_live_backend

    # Keep gated-action writes outside the project's real results directory.
    # Repeated checks may append here, but that cannot affect run_case's return value.
    print("\nSCRIPTED RUN 1")
    run_1, failures_1 = _run_once(case_ids, ISOLATED_RESULTS / "run_1")

    print("\nSCRIPTED RUN 2")
    run_2, failures_2 = _run_once(case_ids, ISOLATED_RESULTS / "run_2")

    RUN_1_PATH.write_text(
        json.dumps(run_1, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    RUN_2_PATH.write_text(
        json.dumps(run_2, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    stable_1 = _without_runtime_timestamp(run_1)
    stable_2 = _without_runtime_timestamp(run_2)
    differing_case_ids = [
        case_id
        for case_id, first, second in zip(case_ids, stable_1, stable_2)
        if first != second
    ]
    decisions_hash_after = _sha256(ORIGINAL_DECISIONS)

    passed = (
        len(run_1) == 42
        and len(run_2) == 42
        and not failures_1
        and not failures_2
        and stable_1 == stable_2
        and decisions_hash_before == decisions_hash_after
    )
    report = {
        "status": "PASS" if passed else "FAIL",
        "backend": "scripted",
        "network_forbidden": True,
        "api_key_removed_from_process": True,
        "expected_cases_per_run": 42,
        "run_1_completed": len(run_1),
        "run_2_completed": len(run_2),
        "run_1_failures": failures_1,
        "run_2_failures": failures_2,
        "identical_excluding_runtime_ts": stable_1 == stable_2,
        "raw_records_identical": run_1 == run_2,
        "differing_case_ids_excluding_runtime_ts": differing_case_ids,
        "original_results_unchanged": decisions_hash_before == decisions_hash_after,
    }
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("\nSTEP 4 RESULT")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Run 1: {RUN_1_PATH}")
    print(f"Run 2: {RUN_2_PATH}")
    print(f"Report: {REPORT_PATH}")

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
