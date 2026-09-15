"""D2(c) · Sequential vs parallel, measured on the same calls.

    python3 evaluation/measure_d2c.py

Scripted backend, no API key, US$0.00, deterministic.

Why a driver rather than Guards(parallel=False). The loop's sequential mode takes the first call
of a reply and discards the rest (`batch = calls if g.parallel else calls[:1]`). Replaying the
recorded transcript that way runs off the end of the recording — the reply for turn 7 assumes the
calls dropped from turn 3 already happened, so the run dies with "no recorded response". That
crash IS D2(c)'s thesis arriving as an exception: sequential execution needs more round trips than
parallel, and a recording made in parallel does not contain them.

So both arms here replay the SAME tool calls, in the SAME order, from the SAME recording. The only
difference is how many calls are allowed to share one model round trip:

    parallel    turn 2 = lookup_policy | get_hospital_status | check_claim_history
    sequential  turn 2 = lookup_policy, turn 3 = get_hospital_status, turn 4 = check_claim_history

Every observation is real — the tools genuinely execute — and every token count is real, because
the message history is rebuilt turn by turn and re-sent exactly as the loop would send it.

**The limit, stated up front:** this measures what the identical work costs under two scheduling
strategies. It does not measure whether a live model told to work sequentially would choose the
same calls. That question needs a second live recording and belongs to the battery, not here.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))

import backends   # noqa: E402
import loop       # noqa: E402
import tools      # noqa: E402

KEYS = json.load(open(os.path.join(_HERE, "..", "A2_reference_data",
                                   "expected_outcomes_A.json"), encoding="utf-8"))
if not isinstance(KEYS, list):
    KEYS = KEYS.get("cases", list(KEYS.values()))
EXPECTED = {k["case_id"]: k["expected_decision"] for k in KEYS}

REPLIES = defaultdict(dict)
with open(os.path.join(_HERE, "transcripts.jsonl"), encoding="utf-8") as fh:
    for line in fh:
        if line.strip():
            row = json.loads(line)
            REPLIES[row["case_id"]][row["turn"]] = row["text"]


def render(name, args, kwargs):
    """Turn a parsed call back into the Action syntax the loop's parser accepts.

    repr() is the right renderer because _parse_call reads arguments with ast.literal_eval,
    so a Python literal round-trips exactly.
    """
    parts = [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
    return f"{name}({', '.join(parts)})"


# A single fixed thought is used for every synthesised reply in all three comparison arms.
# This is the control. The model's real thoughts vary in length from one reply to the next, and
# they land in the message history, so leaving them in would let prose length leak into a
# measurement that is supposed to isolate ONE variable: how many calls share a round trip.
THOUGHT = "Thought: continuing."


def calls_in_order(case_id):
    """Every tool call the recorded run made, in order, plus the reply that ended the run.

    Replies the parser rejects contribute no calls. They cost a round trip in the real recording,
    but they are a property of that recording rather than of the grouping strategy, so they are
    excluded from all three arms equally.
    """
    ordered, tail = [], []
    for t in sorted(REPLIES[case_id]):
        text = REPLIES[case_id][t]
        try:
            thought, calls, final = loop.parse_response(text)
        except loop.ParseError:
            continue
        if final is not None:
            tail.append(text)
            break
        ordered.extend(calls)
    return ordered, tail


def recorded_batches(case_id):
    """The grouping the model actually chose."""
    batches = []
    for t in sorted(REPLIES[case_id]):
        try:
            thought, calls, final = loop.parse_response(REPLIES[case_id][t])
        except loop.ParseError:
            continue
        if final is not None:
            break
        if calls:
            batches.append(calls)
    return batches


def rule_batches(case_id):
    """The largest batches DEPENDS_ON permits, over the same calls in the same order.

    The rule, from docs/D2-tool-layer.md: two calls may share a turn only when neither consumes
    the other's output. A call may join the batch being built only if every tool it depends on
    was satisfied by an EARLIER batch, never by one in the same turn. issue_decision_letter always
    takes its own turn: it is the gated write and the gate reads the whole evidence trail.
    """
    ordered, _ = calls_in_order(case_id)
    batches, done, current = [], set(), []
    for call in ordered:
        name = call[0]
        gated = name in loop.GATED_TOOLS
        if gated or not set(loop.DEPENDS_ON.get(name, ())) <= done:
            if current:
                batches.append(current)
                done.update(c[0] for c in current)
                current = []
            if gated:
                batches.append([call])
                done.add(name)
                continue
        current.append(call)
    if current:
        batches.append(current)
    return batches


def script_for(case_id, mode):
    """Build the reply script for one arm. Every arm replays the SAME calls in the SAME order;
    only the batching differs, and every synthesised reply carries the same fixed thought."""
    if mode == "verbatim":            # used only to prove the driver reproduces a real run
        return [REPLIES[case_id][t] for t in sorted(REPLIES[case_id])]
    ordered, tail = calls_in_order(case_id)
    if mode == "sequential":
        batches = [[c] for c in ordered]
    elif mode == "as_recorded":
        batches = recorded_batches(case_id)
    elif mode == "by_rule":
        batches = rule_batches(case_id)
    else:
        raise ValueError(mode)
    replies = [THOUGHT + "\nAction:\n" + "\n".join(render(*c) for c in batch)
               for batch in batches]
    return replies + tail


@contextlib.contextmanager
def driven_by(replies):
    """Serve a fixed reply list, and keep the irreversible append off the real results file."""
    real, original = backends.complete, tools._RESULTS
    state = {"i": 0}

    def complete(messages, *, model=backends.MODEL, backend=None, case_id=None, turn=None):
        text = replies[min(state["i"], len(replies) - 1)]
        state["i"] += 1
        # Counted per message, exactly as _scripted_complete does: estimate_tokens floors at
        # len//4, so summing per message and joining first give different totals. Matching the
        # real backend is what lets this driver be checked against an ordinary scripted run.
        return {"text": text,
                "tokens_in": sum(backends.estimate_tokens(m["content"]) for m in messages),
                "tokens_out": backends.estimate_tokens(text), "estimated": True}

    with tempfile.TemporaryDirectory() as tmp:
        backends.complete, tools._RESULTS = complete, tmp
        try:
            yield
        finally:
            backends.complete, tools._RESULTS = real, original


# Cases whose recording never reaches a Final cannot take part in this experiment. Their
# synthesised script has no terminating reply, so every arm would spin to the step cap and the
# comparison would measure the cap rather than the grouping. These are the document deadlocks
# described in loop.Guards: the model burns every call available without concluding. They are
# named here rather than silently dropped, and they are still counted in the pass rate the
# harness reports — this exclusion is local to the sequential-vs-parallel measurement.
NO_FINAL = sorted(c for c in REPLIES if not calls_in_order(c)[1])


def arm(mode):
    # The verbatim arm exists only to prove the driver reproduces an ordinary scripted run, so
    # it must run under the SHIPPED guards — the run it is being compared against. The three
    # synthesised arms run with the caps lifted, because the sequential arm deliberately needs
    # more round trips than the shipped call cap allows and truncating it would measure the cap.
    guards = loop.Guards() if mode == "verbatim" else loop.Guards(
        step_cap=40, call_cap=60, budget_ceiling_usd=10.0)
    per_case, turns, tin, tout, cost, correct = {}, [], 0, 0, 0.0, 0
    for key in KEYS:
        case_id = key["case_id"]
        # The verbatim arm must cover all 42: it is checked against an ordinary scripted run,
        # which also runs all 42. Only the synthesised arms drop the non-terminating cases.
        if mode != "verbatim" and case_id in NO_FINAL:
            continue
        with driven_by(script_for(case_id, mode)):
            with contextlib.redirect_stdout(io.StringIO()):
                record = loop.run_case(case_id, guards=guards)
        u = record["usage"]
        turns.append(u["turns"])
        tin += u["tokens_in"]
        tout += u["tokens_out"]
        cost += u["cost_usd"]
        ok = record["decision"] == EXPECTED[case_id]
        correct += 1 if ok else 0
        per_case[case_id] = {"turns": u["turns"], "tokens_in": u["tokens_in"],
                             "cost_usd": round(u["cost_usd"], 6),
                             "decision": record["decision"], "matches_key": ok}
    turns.sort()
    return {"turns_median": turns[len(turns) // 2], "turns_total": sum(turns),
            "turns_max": turns[-1], "tokens_in": tin, "tokens_out": tout,
            "cost_usd": round(cost, 6), "decisions_correct": correct,
            "cases": len(per_case), "per_case": per_case}


SEQ = arm("sequential")
PAR = arm("as_recorded")
RULE = arm("by_rule")

# Sanity: the parallel arm is driven by the recording verbatim, so it must reproduce the ordinary
# scripted run. If this drifts, the driver is lying and nothing below it means anything.
VERBATIM = arm("verbatim")
with contextlib.redirect_stdout(io.StringIO()):
    baseline = [loop.run_case(k["case_id"]) for k in KEYS]
BASE_TOKENS = sum(r["usage"]["tokens_in"] for r in baseline)
BASE_CORRECT = sum(1 for r, k in zip(baseline, KEYS) if r["decision"] == k["expected_decision"])
DRIVER_OK = (BASE_TOKENS == VERBATIM["tokens_in"] and BASE_CORRECT == VERBATIM["decisions_correct"])

disagree = [c for c in PAR["per_case"]
            if PAR["per_case"][c]["decision"] != SEQ["per_case"][c]["decision"]]

# Where parallelising COST us: cases that finished in fewer turns than the calls they paid for.
regressions = sorted(
    ((c, PAR["per_case"][c]["tokens_in"] - SEQ["per_case"][c]["tokens_in"], c)
     for c in PAR["per_case"] if PAR["per_case"][c]["tokens_in"] > SEQ["per_case"][c]["tokens_in"]),
    key=lambda r: -r[1])

print("\nD2(c) · sequential vs parallel — identical calls, identical order, different grouping\n")
print(f"excluded, no Final in the recording so no arm can terminate: {len(NO_FINAL)} "
      f"{NO_FINAL}\nmeasured on the remaining {len(KEYS) - len(NO_FINAL)} cases\n")
print(f"driver reproduces the ordinary scripted run: {'YES' if DRIVER_OK else 'NO — STOP'}")
print(f"  verbatim replay {VERBATIM['tokens_in']} input tokens / {VERBATIM['decisions_correct']} correct"
      f"  vs ordinary scripted run {BASE_TOKENS} / {BASE_CORRECT}\n")
print(f"{'':12s} {'turns med':>10s} {'turns tot':>10s} {'tokens in':>11s} {'tokens out':>11s} {'cost':>10s} {'decisions':>10s}")
for label, a in (("sequential", SEQ), ("as recorded", PAR), ("by rule", RULE)):
    print(f"{label:12s} {a['turns_median']:>10d} {a['turns_total']:>10d} {a['tokens_in']:>11d} "
          f"{a['tokens_out']:>11d} {'$'+format(a['cost_usd'],'.5f'):>10s} "
          f"{str(a['decisions_correct'])+'/'+str(a['cases']):>10s}")
def saving(a):
    return (1 - a["turns_total"] / SEQ["turns_total"],
            1 - a["tokens_in"] / SEQ["tokens_in"],
            1 - a["cost_usd"] / SEQ["cost_usd"])
for label, a in (("as recorded", PAR), ("by rule", RULE)):
    t, k, c = saving(a)
    print(f"\n{label:12s} saves {t:>5.1%} of turns, {k:>5.1%} of input tokens, {c:>5.1%} of cost"
          f"  (vs sequential)")
print(f"decisions that differ between the two arms: {len(disagree)} {disagree if disagree else ''}")
print(f"\ncases where parallelising RAISED input tokens: {len(regressions)}")
for case_id, delta, _ in regressions[:6]:
    print(f"  {case_id}  +{delta} tokens  (parallel {PAR['per_case'][case_id]['turns']} turns, "
          f"sequential {SEQ['per_case'][case_id]['turns']})")

rule_disagree = [c for c in PAR["per_case"]
                 if RULE["per_case"][c]["decision"] != PAR["per_case"][c]["decision"]]
print(f"decisions that differ, by-rule vs as-recorded: {len(rule_disagree)} "
      f"{rule_disagree if rule_disagree else ''}")

out = os.path.join(_HERE, "d2c_run.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"sequential": SEQ, "parallel": PAR, "driver_reproduces_baseline": DRIVER_OK,
               "by_rule": RULE, "excluded_no_final": NO_FINAL,
               "decisions_differing": disagree,
               "parallel_regressions": [{"case_id": c, "extra_input_tokens": d}
                                        for c, d, _ in regressions]}, fh, indent=2)
print(f"\nWritten to {out}")
