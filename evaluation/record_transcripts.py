from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

sys.path.insert(0, str(SRC))
load_dotenv(ROOT / ".env")

import backends  # noqa: E402
import loop  # noqa: E402

# The ONLY place that may switch recording on. See backends.RECORD_TRANSCRIPTS for why.
backends.RECORD_TRANSCRIPTS = True


ANSWER_KEY = ROOT / "A2_reference_data" / "expected_outcomes_A.json"
TRANSCRIPTS = ROOT / "evaluation" / "transcripts.jsonl"
FAILURES = ROOT / "evaluation" / "recording_failures.json"
META = ROOT / "evaluation" / "transcripts.meta.json"

# Confirm this model with the team before spending credit.
MODEL_ID = "google/gemini-2.5-flash-lite"

# First run: leave this as None to run all 42.
# For retries, replace None with a set such as:
# ONLY_CASES = {"CLM-8888", "CLM-9034"}
# First run: leave this as None to run all 42.
# For retries, replace None with a set such as: {"CLM-8888", "CLM-9034"}
ONLY_CASES = None

# Caps used WHILE RECORDING — deliberately far above anything we intend to ship.
#
# The recording is keyed by (case_id, turn), so replay can only serve turns that were
# recorded. A run truncated by a tight cap ends exactly where the cap stopped it, with no
# spare turns — which means the shipped cap can never afterwards be raised and tested for
# free, and the measured turn distribution is censored by the very number it is supposed to
# inform. Record long, ship short: with headroom in the file, any cap at or below the
# recorded length can be evaluated on the scripted backend at zero cost.
#
# budget_ceiling_usd stays the real backstop. It is the guard that caught the 60-call
# runaway on CLM-8850, and it is the reason recording long is safe rather than reckless.
RECORDING_GUARDS = loop.Guards(
    step_cap=20,
    call_cap=30,
    budget_ceiling_usd=0.05,
)


def load_case_ids() -> list[str]:
    with ANSWER_KEY.open("r", encoding="utf-8") as file:
        rows = json.load(file)

    case_ids = [row["case_id"] for row in rows]

    if len(case_ids) != 42:
        raise RuntimeError(
            f"Expected 42 cases, but found {len(case_ids)} in {ANSWER_KEY}"
        )

    if len(case_ids) != len(set(case_ids)):
        raise RuntimeError("The answer key contains duplicate case ids")

    return case_ids


def remove_existing_transcript(case_id: str) -> None:
    """Remove partial recordings before retrying one case."""
    if not TRANSCRIPTS.exists():
        return

    kept_lines = []

    for line in TRANSCRIPTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        row = json.loads(line)

        if row.get("case_id") != case_id:
            kept_lines.append(line)

    text = "\n".join(kept_lines)

    if text:
        text += "\n"

    TRANSCRIPTS.write_text(text, encoding="utf-8")


def _write_provenance(recorded: list[str]) -> None:
    """Say which model produced the recording, and when.

    Without this the transcripts are anonymous, and every scripted number in the report — the
    pass rate, the turn distribution, both D7 failures — rests on a file that cannot be
    attributed to anything. The report has to name the model that generated them.
    """
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        commit = "unknown"

    META.write_text(json.dumps({
        "model": MODEL_ID,
        "backend": "openrouter",
        "temperature": 0,
        "prompt_version": "v2",
        "recorded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": commit,
        # Count the FILE, not this run. A retry re-records a handful of cases, and reporting
        # those as the coverage would understate a complete recording as a partial one.
        "cases_recorded": len({
            json.loads(line)["case_id"]
            for line in TRANSCRIPTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }),
        "replies_recorded": sum(
            1 for line in TRANSCRIPTS.read_text(encoding="utf-8").splitlines() if line.strip()
        ),
        "last_rerecorded": sorted(recorded),
        "note": (
            "Replayed by backends._scripted_complete. These are real replies from the model "
            "named above, including its mistakes - they are NOT written from the answer key, "
            "which is what makes every scripted number a measurement and not a tautology."
        ),
    }, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError(
            "OPENROUTER_API_KEY was not loaded. Check the root .env file."
        )

    all_case_ids = load_case_ids()

    if ONLY_CASES is None:
        selected_case_ids = all_case_ids
    else:
        unknown = set(ONLY_CASES) - set(all_case_ids)

        if unknown:
            raise RuntimeError(f"Unknown case ids: {sorted(unknown)}")

        selected_case_ids = [
            case_id
            for case_id in all_case_ids
            if case_id in ONLY_CASES
        ]

    succeeded = []
    failed = {}

    for number, case_id in enumerate(selected_case_ids, start=1):
        print(
            f"\n[{number}/{len(selected_case_ids)}] "
            f"Recording {case_id}..."
        )

        # Important for retries: do not mix two attempts of the same case.
        remove_existing_transcript(case_id)

        try:
            result = loop.run_case(
                case_id,
                backend="openrouter",
                model=MODEL_ID,
                guards=RECORDING_GUARDS,
            )

            succeeded.append(case_id)
            print(
                f"OK: {case_id} -> "
                f"{result.get('decision', 'no decision')}"
            )

        except Exception as error:
            failed[case_id] = (
                f"{type(error).__name__}: {error}"
            )

            print(f"FAILED: {case_id}")
            traceback.print_exc()

    FAILURES.write_text(
        json.dumps(failed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    _write_provenance(succeeded)

    print("\nRecording complete")
    print(f"Succeeded: {len(succeeded)}")
    print(f"Failed: {len(failed)}")
    print(f"Transcript: {TRANSCRIPTS}")
    print(f"Failure list: {FAILURES}")

    if failed:
        print("\nCases to fix and rerun:")

        for case_id, error in failed.items():
            print(f"- {case_id}: {error}")

        raise SystemExit(1)


if __name__ == "__main__":
    main()
