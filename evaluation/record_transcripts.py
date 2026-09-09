from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

sys.path.insert(0, str(SRC))
load_dotenv(ROOT / ".env")

import loop  # noqa: E402


ANSWER_KEY = ROOT / "A2_reference_data" / "expected_outcomes_A.json"
TRANSCRIPTS = ROOT / "evaluation" / "transcripts.jsonl"
FAILURES = ROOT / "evaluation" / "recording_failures.json"

# Confirm this model with the team before spending credit.
MODEL_ID = "google/gemini-2.5-flash-lite"

# First run: leave this as None to run all 42.
# For retries, replace None with a set such as:
# ONLY_CASES = {"CLM-8888", "CLM-9034"}
ONLY_CASES = None


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
