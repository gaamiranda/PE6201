"""Freeze-checklist item 5 · What the PRICES table implies, so it can be checked against reality.

    python3 evaluation/check_prices.py

Owner: WANG HONGJUN (PLAN.md §5). Free, offline, reads the committed D5(a) trial records.

WHY THIS EXISTS. `backends.price()` raises on an *unknown* model id, so a missing row is loud.
A row that is merely WRONG is silent: it computes, the battery runs, and every cost number in D6
and D7 is off by whatever the error was. This file does not verify prices — nothing offline can.
It prints what the current table implies, so that after checking openrouter.ai/models by hand you
can see immediately whether anything downstream moved.

TWO THINGS DEPEND ON THESE NUMBERS AND ONLY ONE OF THEM IS OBVIOUS.
  1. D6's layer 1 and every projected cost we quote.
  2. `Guards.budget_ceiling_usd`, which must clear the worst single run of the most expensive
     model in the battery. Raise a price enough and the guard starts aborting healthy runs —
     that is not a cost error, it is a harness that stops working mid-battery, on one member's
     machine, after they have spent the money.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

import backends   # noqa: E402
import loop       # noqa: E402

# The models actually fielded. anthropic/claude-haiku-4.5 stays priced in the table because the
# decision to drop it is part of the record (CONTRIBUTIONS.md), but it is not in the battery and
# must not set the ceiling.
BATTERY = [
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat",
    "mistralai/mistral-medium-3",
]
RECORDING_MODEL = "google/gemini-2.5-flash-lite"
NOT_FIELDED = ["anthropic/claude-haiku-4.5"]

TRIALS = os.path.join(_ROOT, "results", "evaluations",
                      "eval-scripted-v2-final.trials.jsonl")
rows = [json.loads(line) for line in open(TRIALS, encoding="utf-8") if line.strip()]
tin = sum(r["tokens_in"] for r in rows)
tout = sum(r["tokens_out"] for r in rows)

print(f"\nPRICES check — {len(rows)} trials, {tin:,} input and {tout:,} output tokens measured\n")
print("Verify each row against openrouter.ai/models. USD per 1,000,000 tokens.\n")
print(f"  {'model':38} {'in':>6} {'out':>6} {'76 trials':>10} {'worst run':>10}")

ceiling = loop.Guards().budget_ceiling_usd
worst_fielded = 0.0
for model in BATTERY + [RECORDING_MODEL] + NOT_FIELDED:
    pin, pout = backends.PRICES[model]
    schedule = backends.price(model, tin, tout)
    worst = max(backends.price(model, r["tokens_in"], r["tokens_out"]) for r in rows)
    if model in BATTERY:
        worst_fielded = max(worst_fielded, worst)
    tag = "" if model in BATTERY else ("   <- recording model, not fielded"
                                       if model == RECORDING_MODEL else "   <- NOT in the battery")
    print(f"  {model:38} {pin:>6.2f} {pout:>6.2f} {schedule:>10.4f} {worst:>10.5f}{tag}")

print(f"\n  Budget ceiling  US${ceiling:.5f}")
print(f"  Worst run in the battery  US${worst_fielded:.5f} "
      f"({100 * (ceiling / worst_fielded - 1):.1f}% headroom)" if worst_fielded else "")
if ceiling > worst_fielded:
    print("  OK — the ceiling clears every fielded model.\n")
else:
    print("  ⚠ THE CEILING NO LONGER CLEARS THE BATTERY. Raising a price has made "
          "Guards.budget_ceiling_usd\n    abort healthy runs. Re-derive it in src/loop.py "
          "BEFORE anyone spends, or the battery dies mid-run.\n")

print("  These figures price the SCRIPTED token counts at each model's rate. A live model that")
print("  takes more turns costs more — NIU TONG's smoke test used 15 model calls on a case where")
print("  gemini's median is 7. Treat them as a floor, and report the gap in D6.\n")
