"""D7 failure 2 · Tool interface — the working agent, minus the v2 check_coverage shape.

    python3 evaluation/reproduce_failure_2.py

Scripted backend, no API key, US$0.00, deterministic. Output is written to
`evaluation/failure_2_run.json`.

THE DELETION
    `check_coverage` goes back to the pre-rewrite return shape — five flat fields, one per
    branch signal:

        {"code", "covered", "exclusion", "requires_preauth", "document_required"}

    instead of the shipped one, where a refused line has nowhere to carry follow-up work:

        {"code", "coverage": {"status", "exclusion"}, "needed_next": [...]}

    Putting the v2 shape back recovers the behaviour, which is what makes this a deletion from
    the working agent rather than a separately written bad one.

WHY THREE ARMS AND NOT TWO
    The rewrite changed two things at once: the returned object and the descriptor prose that
    documents it. D2(b) measures the prose. This file measures the shape, so the middle arm
    holds the v2 descriptor fixed and swaps only the object — the difference is then
    attributable to the shape alone. The third arm reverts both, which is what the repository
    actually looked like at `91da36f`.

WHAT THE SCRIPTED BACKEND CAN AND CANNOT SHOW HERE
    `transcripts.jsonl` is keyed on `(case_id, turn)` alone, so the model's replies are fixed no
    matter what the tool layer returns underneath them. Decision and pass rates therefore CANNOT
    move, and the fact that they do not is a property of the instrument, not evidence about the
    fix. What does move is real and is the point: the size of the observation the model is
    charged for on every line of every run, and the number of observations that state a
    contradiction.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import runpy

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "harness"))

import backends   # noqa: E402
import loop       # noqa: E402
import tools      # noqa: E402
import run_eval   # noqa: E402

KEYS = json.load(open(os.path.join(_ROOT, "A2_reference_data",
                                   "expected_outcomes_A.json"), encoding="utf-8"))
if not isinstance(KEYS, list):
    KEYS = KEYS.get("cases", list(KEYS.values()))


# ── The deleted shape, verbatim from 91da36f ─────────────────────────────────

def check_coverage_v1(policy_id: str, procedure_code: str):
    """Decide ONE line against ONE policy: covered, and what the line needs next."""
    pol = tools._POLICIES.get(policy_id)
    if pol is None:
        raise tools.ToolError(f"no policy with id {policy_id}")
    proc = tools._PROCEDURES.get(procedure_code)
    if proc is None:
        raise tools.ToolError(f"no procedure with code {procedure_code}")

    exclusion = next((e["rule"] for e in pol["exclusions"] if e["code"] == procedure_code), None)

    # Nothing here couples the branch flags to `covered`. A line can leave this function
    # refused AND carrying two demands for paperwork at the same time. That is the defect.
    return {
        "code": procedure_code,
        "covered": exclusion is None,
        "exclusion": exclusion,
        "requires_preauth": bool(proc["requires_preauth"]),
        "document_required": tools._REQUIRED_DOCS.get(procedure_code),
    }


# Shape-only arm: same function body, but wearing the SHIPPED descriptor, so the tool manual
# the model is charged for is byte-identical across the two arms and only the observation moves.
def _shape_only():
    def check_coverage(policy_id: str, procedure_code: str):
        return check_coverage_v1(policy_id, procedure_code)
    check_coverage.__doc__ = tools.check_coverage.__doc__
    check_coverage.__name__ = "check_coverage"
    return check_coverage


V2 = tools.TOOLS["check_coverage"]
ARMS = {
    "fixed_v2_shape": V2,                 # shipped
    "broken_shape_only": _shape_only(),   # v1 object, v2 descriptor — the attributable arm
    "broken_full_v1": check_coverage_v1,  # v1 object AND v1 descriptor — the repo at 91da36f
}


@contextlib.contextmanager
def coverage_is(fn):
    tools.TOOLS["check_coverage"] = fn
    tools.check_coverage = fn
    try:
        yield
    finally:
        tools.TOOLS["check_coverage"] = V2
        tools.check_coverage = V2


@contextlib.contextmanager
def isolated_decision_log():
    original = tools._RESULTS
    with tempfile.TemporaryDirectory() as tmp:
        tools._RESULTS = tmp
        try:
            yield os.path.join(tmp, "decisions.jsonl")
        finally:
            tools._RESULTS = original


# ── A · the interface census: how many observations can state a contradiction ──
#
# This is the one measurement that does not depend on a model at all. Every line of every
# evaluation case is put through both shapes and the contradictory ones are counted: refused,
# and simultaneously asking the agent to chase pre-authorisation or a document for the line it
# just refused.

def census():
    total_lines, contradictory, cases_hit = 0, [], set()
    for key in KEYS:
        try:
            claim = tools.get_claim(key["case_id"])
        except tools.ToolError:
            continue
        policy = tools.lookup_policy(claim["member_id"], claim["date_of_service"])
        for line in claim["lines"]:
            total_lines += 1
            try:
                old = check_coverage_v1(policy["policy_id"], line["code"])
                new = V2(policy["policy_id"], line["code"])
            except tools.ToolError:
                continue
            if not old["covered"] and (old["requires_preauth"] or old["document_required"]):
                contradictory.append({
                    "case_id": key["case_id"], "code": line["code"],
                    "old": old, "new": new,
                })
                cases_hit.add(key["case_id"])
    return {"lines_checked": total_lines,
            "contradictory_observations": len(contradictory),
            "cases_affected": sorted(cases_hit),
            "examples": contradictory[:3]}


# Whole-fixture version: not just the lines our cases happen to use, but every policy x
# procedure pair the tool could ever be asked about. The evaluation set is 42 cases; the
# interface is the whole product space, and that is what a shape makes impossible.
def census_all_pairs():
    total, bad = 0, 0
    for policy_id in tools._POLICIES:
        for code in tools._PROCEDURES:
            total += 1
            old = check_coverage_v1(policy_id, code)
            if not old["covered"] and (old["requires_preauth"] or old["document_required"]):
                bad += 1
    return {"pairs": total, "contradictory_pairs": bad,
            "percent": round(100.0 * bad / total, 2) if total else 0.0}


# ── B · observation size, paid once per line per run ─────────────────────────

def observation_bytes():
    out = {}
    for name, fn in ARMS.items():
        if name == "broken_full_v1":
            continue
        chars, toks, n = 0, 0, 0
        for key in KEYS:
            try:
                claim = tools.get_claim(key["case_id"])
            except tools.ToolError:
                continue
            policy = tools.lookup_policy(claim["member_id"], claim["date_of_service"])
            for line in claim["lines"]:
                try:
                    text = json.dumps(fn(policy["policy_id"], line["code"]), ensure_ascii=False)
                except tools.ToolError:
                    continue
                chars += len(text)
                toks += backends.estimate_tokens(text)
                n += 1
        out[name] = {"observations": n, "chars": chars, "estimated_tokens": toks,
                     "mean_chars": round(chars / n, 1) if n else 0.0}
    return out


# ── B2 · the tool manual, which is re-sent on EVERY model call ───────────────
#
# The third arm reverts the descriptor as well as the shape, so its token total must be
# decomposed or it will be read as evidence about the shape. The manual is built live off the
# docstrings, so measuring it settles the attribution.

def manual_tokens():
    out = {}
    for name, fn in ARMS.items():
        with coverage_is(fn):
            out[name] = backends.estimate_tokens(loop.tool_manual("v2"))
    return out


# ── C · the whole 42-case set through the real harness, under each shape ─────

def harness_run(label):
    with tempfile.TemporaryDirectory() as tmp:
        with contextlib.redirect_stdout(io.StringIO()):
            code = run_eval.main(["--backend", "scripted", "--output-dir", tmp,
                                  "--run-id", label])
        if code != 0:
            raise SystemExit(f"harness exited {code} for arm {label}")
        summary_file = next(p for p in os.listdir(tmp) if p.endswith(".summary.json"))
        s = json.load(open(os.path.join(tmp, summary_file), encoding="utf-8"))
    return {
        "code_pass": s["provisional_code_only_passed_trial_count"],
        "trials": s["total_trial_count"],
        "decision_cases_pass": s["decision_only_cases_passed"],
        "cases": s["unique_case_count"],
        "tokens_in": s["total_input_tokens"],
        "tokens_out": s["total_output_tokens"],
        "projected_schedule_usd": round(s["projected_cost_76_trial_schedule_usd"], 6),
        "code_failed_cases": sorted(s["provisional_code_failure_reasons"]),
    }


# ── D · the ten-row guardrail checklist, under each shape ────────────────────
#
# Run from a copy in a throwaway directory so the committed guardrail_checklist_run.json —
# D3(b) evidence — is never overwritten by a D7 experiment.

def guardrail(label):
    with tempfile.TemporaryDirectory() as tmp:
        script = os.path.join(tmp, "run_guardrail_checklist.py")
        shutil.copy(os.path.join(_HERE, "run_guardrail_checklist.py"), script)
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(script, run_name="__main__")
        report = json.load(open(os.path.join(tmp, "guardrail_checklist_run.json"),
                                encoding="utf-8"))
    return {"passed": report["passed"], "total": report["total"],
            "failed_rows": [r["row"] for r in report["rows"] if not r["passed"]]}


# ── Run ──────────────────────────────────────────────────────────────────────

CENSUS = census()
PAIRS = census_all_pairs()
SIZES = observation_bytes()
MANUAL = manual_tokens()

RESULTS = {}
for name, fn in ARMS.items():
    with coverage_is(fn), isolated_decision_log():
        RESULTS[name] = {"harness": harness_run(name), "guardrail": guardrail(name)}

REPORT = {"census_evaluation_set": CENSUS, "census_all_pairs": PAIRS,
          "observation_size": SIZES, "manual_tokens": MANUAL, "arms": RESULTS}

# ── Report ───────────────────────────────────────────────────────────────────

print("\nD7 failure 2 — the working agent, minus the v2 check_coverage return shape\n")

print("A · contradictory observations the old shape can produce")
print(f"  across the 42 evaluation cases : {CENSUS['contradictory_observations']} of "
      f"{CENSUS['lines_checked']} lines, in cases {', '.join(CENSUS['cases_affected']) or '(none)'}")
print(f"  across every policy x procedure: {PAIRS['contradictory_pairs']} of {PAIRS['pairs']} "
      f"pairs ({PAIRS['percent']}%)")
print("  under the shipped shape this count is 0 BY CONSTRUCTION: a not_covered line leaves")
print("  check_coverage with needed_next == [], so the observation cannot be written.\n")

print("B · observation size, paid once per line per run")
old, new = SIZES["broken_shape_only"], SIZES["fixed_v2_shape"]
print(f"  {'old shape':<18} {old['observations']:>4} observations  {old['chars']:>6} chars  "
      f"{old['estimated_tokens']:>5} est. tokens  mean {old['mean_chars']} chars")
print(f"  {'shipped shape':<18} {new['observations']:>4} observations  {new['chars']:>6} chars  "
      f"{new['estimated_tokens']:>5} est. tokens  mean {new['mean_chars']} chars")
delta = old["chars"] - new["chars"]
print(f"  -> the safer shape is also the smaller one by {delta} chars "
      f"({round(100.0*delta/old['chars'], 1)}%)\n" if old["chars"] else "")

print(f"  the tool manual, re-sent on every model call: "
      f"v2 descriptor {MANUAL['fixed_v2_shape']} tokens, "
      f"v1 descriptor {MANUAL['broken_full_v1']} tokens "
      f"(delta {MANUAL['fixed_v2_shape'] - MANUAL['broken_full_v1']}) — "
      f"that delta, not the shape, is\n  what moves arm three's total. See D2(b).\n")

print("C · the whole evaluation set through the harness, each shape")
print(f"  {'arm':<20} {'code':>8} {'decisions':>11} {'tokens in':>11} {'tokens out':>11} "
      f"{'projected 76':>13} {'guardrail':>10}")
for name in ARMS:
    h, g = RESULTS[name]["harness"], RESULTS[name]["guardrail"]
    print(f"  {name:<20} {str(h['code_pass'])+'/'+str(h['trials']):>8} "
          f"{str(h['decision_cases_pass'])+'/'+str(h['cases']):>11} "
          f"{h['tokens_in']:>11d} {h['tokens_out']:>11d} "
          f"{'$'+format(h['projected_schedule_usd'], '.6f'):>13} "
          f"{str(g['passed'])+'/'+str(g['total']):>10}")

base = RESULTS["fixed_v2_shape"]["harness"]
same = all(RESULTS[n]["harness"]["code_pass"] == base["code_pass"]
           and RESULTS[n]["harness"]["decision_cases_pass"] == base["decision_cases_pass"]
           for n in ARMS)
print("\n  pass rates identical across all three arms: "
      + ("yes — and that is the instrument, not the fix. transcripts.jsonl is keyed on\n"
         "       (case_id, turn) alone, so replay is blind to the tool layer underneath it."
         if same else "NO — investigate, replay was expected to be blind to this"))

out = os.path.join(_HERE, "failure_2_run.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(REPORT, fh, indent=2)
print(f"\nWritten to {out}")
