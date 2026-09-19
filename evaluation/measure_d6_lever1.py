"""D6 Lever 1 · tool block size, measured as a prompt-prefix replay.

    python3 evaluation/measure_d6_lever1.py

Scripted backend, no API key, US$0.00, deterministic.

This measures the cost of carrying two rejected tools in the tool block. It replays the same
76-trial formal schedule twice:

    shipped            the current v2 tool manual
    fat_tool_block     the current v2 tool manual plus two counterfactual descriptors

The model replies, tool calls, tools, data, guards and prices are otherwise identical. This
isolates the B term in the Class 5 cost model: prompt-prefix text that is re-sent on every model
call. It does not measure how a live model would behave if the rejected tools were actually
available.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))

import backends  # noqa: E402
import loop  # noqa: E402
import tools  # noqa: E402

MODEL = "google/gemini-2.5-flash-lite"
PROMPT_VERSION = "v2"

COUNTERFACTUAL_TOOL_DESCRIPTORS = """check_required_documents(procedure_code)
WHAT               Returns the document required for one procedure code, if any.
INPUT              procedure_code is one claim-line procedure code; an unknown code raises ToolError.
RETURNS            {"procedure_code": str, "document_required": str | null}. One bounded object.
FAILS WHEN         The procedure code is unknown.
IRREVERSIBLE?      No. This only reads fixture data.

lookup_member(member_id)
WHAT               Returns member demographics and join date for one member id.
INPUT              member_id is the member id from get_claim; an unknown id raises ToolError.
RETURNS            {"member_id": str, "name": str, "join_date": str}. One bounded object.
FAILS WHEN         The member id is unknown.
IRREVERSIBLE?      No. This only reads fixture data."""


def load_cases() -> list[dict]:
    with (REPO / "A2_reference_data" / "expected_outcomes_A.json").open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        data = data.get("cases", list(data.values()))
    return data


def formal_schedule(cases: list[dict]) -> list[dict]:
    """D4/D5 formal schedule: ordinary cases once; request/escalate cases three times."""
    schedule: list[dict] = []
    for case in cases:
        repeat = 3 if case["expected_decision"] != "approve_in_principle" else 1
        for trial in range(1, repeat + 1):
            item = dict(case)
            item["trial"] = trial
            schedule.append(item)
    return schedule


@contextlib.contextmanager
def isolated_results_dir():
    original_results = tools._RESULTS
    with tempfile.TemporaryDirectory() as tmp:
        tools._RESULTS = tmp
        try:
            yield
        finally:
            tools._RESULTS = original_results


@contextlib.contextmanager
def manual_variant(kind: str):
    original = loop.tool_manual

    def patched(prompt_version: str = PROMPT_VERSION) -> str:
        manual = original(prompt_version)
        if kind == "fat_tool_block":
            return manual + "\n\n" + COUNTERFACTUAL_TOOL_DESCRIPTORS
        return manual

    loop.tool_manual = patched
    try:
        yield
    finally:
        loop.tool_manual = original


def run_arm(kind: str, schedule: list[dict]) -> dict:
    turns: list[int] = []
    model_calls: list[int] = []
    tokens_in = tokens_out = 0
    cost = 0.0
    decisions_correct = 0
    cap_counts: dict[str, int] = {}
    per_trial = []

    with manual_variant(kind), isolated_results_dir():
        for row in schedule:
            with contextlib.redirect_stdout(io.StringIO()):
                record = loop.run_case(
                    row["case_id"],
                    prompt_version=PROMPT_VERSION,
                    backend="scripted",
                    model=MODEL,
                )
            usage = record["usage"]
            ok = record["decision"] == row["expected_decision"]
            decisions_correct += 1 if ok else 0
            turns.append(usage["turns"])
            model_calls.append(record["model_calls"])
            tokens_in += usage["tokens_in"]
            tokens_out += usage["tokens_out"]
            cost += usage["cost_usd"]
            if usage.get("cap_fired"):
                cap_counts[usage["cap_fired"]] = cap_counts.get(usage["cap_fired"], 0) + 1
            per_trial.append(
                {
                    "case_id": row["case_id"],
                    "trial": row["trial"],
                    "decision": record["decision"],
                    "matches_expected_decision": ok,
                    "turns": usage["turns"],
                    "model_calls": record["model_calls"],
                    "tokens_in": usage["tokens_in"],
                    "tokens_out": usage["tokens_out"],
                    "cost_usd": round(usage["cost_usd"], 6),
                    "cap_fired": usage.get("cap_fired"),
                }
            )

    turns_sorted = sorted(turns)
    calls_sorted = sorted(model_calls)
    return {
        "manual_estimated_tokens": backends.estimate_tokens(loop.tool_manual(PROMPT_VERSION))
        if kind == "shipped"
        else backends.estimate_tokens(loop.tool_manual(PROMPT_VERSION) + "\n\n" + COUNTERFACTUAL_TOOL_DESCRIPTORS),
        "trials": len(schedule),
        "turns_median": turns_sorted[len(turns_sorted) // 2],
        "turns_total": sum(turns),
        "model_calls_median": calls_sorted[len(calls_sorted) // 2],
        "model_calls_total": sum(model_calls),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost, 6),
        "decisions_correct": decisions_correct,
        "decision_rate": decisions_correct / len(schedule),
        "cap_counts": cap_counts,
        "per_trial": per_trial,
    }


def main() -> None:
    cases = load_cases()
    schedule = formal_schedule(cases)
    shipped = run_arm("shipped", schedule)
    fat = run_arm("fat_tool_block", schedule)

    result = {
        "purpose": "D6 Lever 1 tool block size measurement.",
        "method": (
            "Replay the same 76-trial scripted schedule with the shipped v2 tool manual and with "
            "a counterfactual fat tool block that appends two rejected tool descriptors. This "
            "isolates prompt-prefix cost; it does not re-measure live model behaviour."
        ),
        "model": MODEL,
        "backend": "scripted",
        "prompt_version": PROMPT_VERSION,
        "counterfactual_descriptors": COUNTERFACTUAL_TOOL_DESCRIPTORS.splitlines(),
        "shipped": shipped,
        "fat_tool_block": fat,
        "delta_fat_minus_shipped": {
            "manual_estimated_tokens": fat["manual_estimated_tokens"] - shipped["manual_estimated_tokens"],
            "tokens_in": fat["tokens_in"] - shipped["tokens_in"],
            "tokens_out": fat["tokens_out"] - shipped["tokens_out"],
            "cost_usd": round(fat["cost_usd"] - shipped["cost_usd"], 6),
            "turns_total": fat["turns_total"] - shipped["turns_total"],
            "model_calls_total": fat["model_calls_total"] - shipped["model_calls_total"],
            "decisions_correct": fat["decisions_correct"] - shipped["decisions_correct"],
        },
        "interpretation": (
            "The rejected tools affect the B term only: extra prompt-prefix text is re-sent on "
            "each model call. In this replay, adding the two descriptors changes input tokens and "
            "projected cost, but not the replayed decisions, turns, model calls or output tokens."
        ),
    }

    out = HERE / "d6_lever1_run.json"
    with out.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")

    print("D6 Lever 1 measurement written to", out)
    print("shipped tokens_in", shipped["tokens_in"], "cost", shipped["cost_usd"])
    print("fat     tokens_in", fat["tokens_in"], "cost", fat["cost_usd"])
    print("delta   tokens_in", result["delta_fat_minus_shipped"]["tokens_in"],
          "cost", result["delta_fat_minus_shipped"]["cost_usd"])


if __name__ == "__main__":
    main()
