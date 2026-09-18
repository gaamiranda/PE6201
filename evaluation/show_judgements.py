"""Print a judgement queue in a readable shape so the 12 rows can be judged quickly.

Read-only. It changes nothing: you fill judgement_pass / reviewer / reviewer_notes in the
.judgement-queue.jsonl yourself, then re-run run_eval.py with --input-results and --judgements.

    python3 evaluation/show_judgements.py results/evaluations/<your-run>.judgement-queue.jsonl
    python3 evaluation/show_judgements.py <file> --unfilled     # only the rows still blank
"""
from __future__ import annotations

import argparse
import json
import sys

BOLD, DIM, OFF = "\033[1m", "\033[2m", "\033[0m"


def main() -> None:
    ap = argparse.ArgumentParser(description="Show a judgement queue readably")
    ap.add_argument("queue")
    ap.add_argument("--unfilled", action="store_true", help="only rows with no verdict yet")
    a = ap.parse_args()

    rows = [json.loads(line) for line in open(a.queue, encoding="utf-8") if line.strip()]
    shown = 0
    for n, row in enumerate(rows, start=1):
        if a.unfilled and row.get("judgement_pass") is not None:
            continue
        shown += 1
        verdict = row.get("judgement_pass")
        mark = "…" if verdict is None else ("PASS" if verdict else "FAIL")
        print(f"\n{BOLD}[{n}/{len(rows)}] {row['case_id']} trial {row['trial']}{OFF}   {mark}")

        print(f"\n  {BOLD}Must record{OFF}")
        for item in row.get("must_record") or []:
            print(f"    · {item}")

        print(f"\n  {BOLD}The record the agent produced{OFF}")
        record = row.get("structured_final_record")
        text = json.dumps(record, indent=2, ensure_ascii=False, default=str)
        for line in text.splitlines():
            print(f"    {DIM}{line}{OFF}")

        if row.get("reviewer_notes"):
            print(f"\n  {BOLD}Notes{OFF} ({row.get('reviewer')}) {row['reviewer_notes']}")
        print("\n" + "─" * 78)

    rule = rows[0].get("judgement_rule") if rows else None
    print(f"\n{BOLD}The rule{OFF}\n  {rule}\n")
    blank = sum(1 for r in rows if r.get("judgement_pass") is None)
    print(f"{shown} shown · {len(rows)} rows · {BOLD}{blank} still unjudged{OFF}")
    print("\nFill judgement_pass (true/false), reviewer and reviewer_notes on each row, then:")
    print(f"  python3 harness/run_eval.py --input-results <run>.trials.jsonl \\\n"
          f"      --judgements {a.queue} --run-id <yourname>-final --output-dir results/evaluations\n")


if __name__ == "__main__":
    main()
