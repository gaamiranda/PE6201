"""D7 failure 1 · Loop control — the working agent, minus action de-duplication.

    python3 evaluation/reproduce_failure_1.py

Scripted backend, no API key, US$0.00, deterministic. A failure built as a deletion is
deterministic by construction, which is the whole reason the brief asks for it that way:
putting `dedup` back must recover the behaviour, and here it does, exactly.

Two measurements, because one of them is the point:

  A · The whole 42-case evaluation set, both ways. De-duplication suppresses NOTHING here.
      The guard looks like dead code right up until part B.
  B · An induced repeat. The same claim is written once with the guard and four times without,
      and not one aggregate number moves.
"""
import contextlib
import io
import json
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))

import backends   # noqa: E402
import loop       # noqa: E402
import tools      # noqa: E402

KEYS = json.load(open(os.path.join(_HERE, "..", "A2_reference_data",
                                   "expected_outcomes_A.json"), encoding="utf-8"))
if not isinstance(KEYS, list):
    KEYS = KEYS.get("cases", list(KEYS.values()))


@contextlib.contextmanager
def isolated_decision_log():
    """Never let a D7 run append to the real results/decisions.jsonl."""
    original = tools._RESULTS
    with tempfile.TemporaryDirectory() as tmp:
        tools._RESULTS = tmp
        try:
            yield os.path.join(tmp, "decisions.jsonl")
        finally:
            tools._RESULTS = original


def fake_model(replies):
    state = {"i": 0}

    def complete(messages, *, model=backends.MODEL, backend=None, case_id=None, turn=None):
        text = replies[min(state["i"], len(replies) - 1)]
        state["i"] += 1
        joined = "".join(m["content"] for m in messages)
        return {"text": text, "tokens_in": backends.estimate_tokens(joined),
                "tokens_out": backends.estimate_tokens(text), "estimated": True}
    return complete


@contextlib.contextmanager
def model_is(replies):
    real = backends.complete
    backends.complete = fake_model(replies)
    try:
        yield
    finally:
        backends.complete = real


# ── A · the whole evaluation set, both ways ──────────────────────────────────

def sweep(dedup):
    guards = loop.Guards(dedup=dedup)
    turns, tool_calls, tin, tout, cost, correct, capped = [], 0, 0, 0, 0.0, 0, 0
    for key in KEYS:
        with contextlib.redirect_stdout(io.StringIO()):
            record = loop.run_case(key["case_id"], guards=guards)
        u = record["usage"]
        turns.append(u["turns"])
        tool_calls += len(u["tools_called"])
        tin += u["tokens_in"]
        tout += u["tokens_out"]
        cost += u["cost_usd"]
        capped += 1 if u.get("cap_fired") else 0
        correct += 1 if record["decision"] == key["expected_decision"] else 0
    turns.sort()
    return {"turns_median": turns[len(turns) // 2], "turns_max": turns[-1],
            "tool_calls": tool_calls, "tokens_in": tin, "tokens_out": tout,
            "cost_usd": round(cost, 6), "decisions_correct": correct,
            "cases": len(KEYS), "cap_fired": capped}


FIXED = sweep(dedup=True)
BROKEN = sweep(dedup=False)
# A suppressed call never reaches tools_called, so equal totals mean zero suppressions.
SUPPRESSED = BROKEN["tool_calls"] - FIXED["tool_calls"]

# ── B · the induced repeat ───────────────────────────────────────────────────
# The gate's evidence precondition demands check_coverage once per reported line and a
# check_claim_history before any approval, so the scripted model earns the write first.
# Otherwise the run is refused one layer earlier and this measures the validator instead.
APPROVAL = {"case_id": "CLM-8842", "decision": "approve_in_principle",
            "reason": "line 47120 covered in full",
            "lines": [{"code": "47120", "status": "covered"}],
            "approved_total": 1400, "refused_total": 0}
LETTER = "Thought: recording it.\nAction: issue_decision_letter(record=" + json.dumps(APPROVAL) + ")"
GROUNDWORK = [
    'Thought: read the claim.\nAction: get_claim(case_id="CLM-8842")',
    'Thought: find the policy.\nAction: lookup_policy(member_id="M-2214", date_of_service="2026-09-02")',
    'Thought: decide the line.\nAction: check_coverage(policy_id="POL-3310", procedure_code="47120")',
    'Thought: check for a duplicate.\nAction: check_claim_history(member_id="M-2214", '
    'hospital_id="H-114", date_of_service="2026-09-02", lines=[{"code": "47120", "amount": 1400}])',
]


def induced(dedup, repeats, then_stop=True):
    tail = ["Thought: done.\nFinal: " + json.dumps(APPROVAL)] if then_stop else [LETTER]
    script = GROUNDWORK + [LETTER] * repeats + tail
    with isolated_decision_log() as log, model_is(script):
        with contextlib.redirect_stdout(io.StringIO()):
            record = loop.run_case("CLM-8842", guards=loop.Guards(dedup=dedup))
        # Counted INSIDE the context: the temporary directory is removed on exit.
        written = 0
        if os.path.exists(log):
            written = sum(1 for line in open(log, encoding="utf-8") if line.strip())
    u = record["usage"]
    return {"letters_written": written, "turns": u["turns"], "tokens_in": u["tokens_in"],
            "cost_usd": round(u["cost_usd"], 6), "decision": record["decision"],
            "cap_fired": u.get("cap_fired"),
            "letter_actions": u["tools_called"].count("issue_decision_letter")}


B_FIXED = induced(dedup=True, repeats=4)
B_BROKEN = induced(dedup=False, repeats=4)
# Left to run forever, which guard stops it, and how much has it already written by then?
RUNAWAY = induced(dedup=False, repeats=40, then_stop=False)

REPORT = {"sweep": {"fixed": FIXED, "broken": BROKEN, "calls_suppressed_across_set": SUPPRESSED},
          "induced": {"fixed": B_FIXED, "broken": B_BROKEN, "runaway_no_dedup": RUNAWAY}}

print("\nD7 failure 1 — the working agent, minus action de-duplication\n")
print("A · whole evaluation set, both ways")
print(f"{'':10s} {'turns med/max':>14s} {'tool calls':>11s} {'tokens in':>10s} {'cost':>10s} {'decisions':>10s}")
for label, s in (("fixed", FIXED), ("broken", BROKEN)):
    print(f"{label:10s} {str(s['turns_median'])+'/'+str(s['turns_max']):>14s} {s['tool_calls']:>11d} "
          f"{s['tokens_in']:>10d} {'$'+format(s['cost_usd'],'.5f'):>10s} "
          f"{str(s['decisions_correct'])+'/'+str(s['cases']):>10s}")
print(f"\n  calls de-duplication suppressed across all {FIXED['cases']} cases: {SUPPRESSED}")
print("  -> on the committed evaluation set the guard is indistinguishable from dead code.\n")

print("B · induced repeat: the same approval action issued 4 times in one run")
print(f"{'':10s} {'letters WRITTEN':>16s} {'write actions':>14s} {'turns':>6s} {'tokens in':>10s} {'cost':>10s}")
for label, s in (("fixed", B_FIXED), ("broken", B_BROKEN)):
    print(f"{label:10s} {s['letters_written']:>16d} {s['letter_actions']:>14d} {s['turns']:>6d} "
          f"{s['tokens_in']:>10d} {'$'+format(s['cost_usd'],'.5f'):>10s}")
print(f"\n  left unbounded, no dedup: {RUNAWAY['letters_written']} letters written before "
      f"{RUNAWAY['cap_fired']} stopped the run at turn {RUNAWAY['turns']}.")
print("  -> the step cap bounds the damage. It does not prevent it.\n")

out = os.path.join(_HERE, "failure_1_run.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(REPORT, fh, indent=2)
print(f"Written to {out}")
