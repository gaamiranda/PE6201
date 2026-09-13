# harness — the evaluation runner

**Owners:** JIN CHENG · NIU TONG. *Deadlines and dependencies: [`../PLAN.md`](../PLAN.md).*

D4 and D5. This is the instrument that makes the whole submission credible.

**You are not blocked on the loop.** [`../src/contracts.py`](../src/contracts.py) is committed and
frozen — `DecisionRecord`, `ExpectedOutcome`, `TrialResult`, `run_case()` and `complete()`. Build
against it now; the loop fills in behind you.

**The answer key is `../A2_reference_data/expected_outcomes_A.json`** — one file, joined on
`case_id`. There is no second key. See [`../evaluation/cases/README.md`](../evaluation/cases/README.md).

> **Updated against the change notice of 1 September 2026** — trial arithmetic, grader names, and
> the rule that every member runs a live model.

## Running it

```bash
python -m unittest discover -s harness -p 'test_*.py'   # 26 tests, offline
python -m harness.run_eval                              # scripted, free, no key
```

**A bare run reports `INCOMPLETE`, and that is correct.** It re-executes the cases, and fresh
trials have no judgement verdicts attached yet, so the combined score cannot be computed. The
harness refuses to print a number it cannot back up rather than quietly reporting the
code-only rate as if it were the final one. To reproduce the committed figure, hand it the
saved judgements:

```bash
python -m harness.run_eval \
  --input-results results/evaluations/eval-scripted-v2-final.trials.jsonl \
  --judgements   results/evaluations/eval-scripted-v2-final.judgements-reviewed.jsonl
```

That prints **49/76 (64.47%)** combined, against **38/42 (90.48%)** on decisions alone. The
distance between those two numbers is the finding, not noise: the agent reaches the right
outcome and then writes a reason that names none of the facts the outcome rests on.

For a live battery, add `--backend openrouter` and the model. Scripted is the default, so it
is entirely possible to follow every instruction, spend nothing, and hand in replayed output
that looks like a real result.

## Requirements it must satisfy

- **`BACKEND = "scripted"` is the default.** Deterministic canned responses, no network, no key, so
  a marker can clone and reproduce every number at zero cost. If the harness does not run this way,
  Technical Execution is **capped**.
- **Isolation** — each case starts from a clean state. No case may depend on a previous one running.
- **Trials: one per ordinary case, three per negative case.** Not three across the board — that was
  the old reading, and it is what made the brief's own budget table wrong.
- **Two kinds of check**, and you need both:
  - **code check** — the harness compares the answer against the answer key. No model, no opinion.
  - **judgement check** — a person, or a second model, reads the record and decides.
  (The brief no longer says "L1 / L2".)
- **Outcome-graded** — `act` / `ask` / `escalate` — and a run that reaches the right outcome by the
  **wrong trigger** is not a pass.

## Instrumentation — per run, every run

Without this a loop failure is invisible: it raises no exception, it just costs more.

```
turns used · tokens in · tokens out · estimated cost · whether a cap fired · tools called, in order
```

## What runs free, and what costs money

Only one part of A2 spends anything. Keep it that way.

| Runs on the scripted backend — free, no key | Costs credit |
|---|---|
| D3(b) the ten guardrail cases | D5(b) the live battery |
| D5(a) the reproducible end-to-end run | |
| D7 both failure reproductions | |

Guardrails are *your* code — a model cannot influence whether a step cap fires — so a deterministic
backend is the *correct* instrument, not merely the cheap one. Same for D7: a failure built as a
deletion is deterministic by construction, so script the observation that causes the loop and it
reproduces for ever at no cost.

**The caveat, which belongs in the report:** a scripted run proves your guardrail fires when the
agent *attempts* a bad action. It cannot tell you whether a live model can be talked into attempting
it. That second question belongs to the D5 battery, not to a guardrail case.

## The live battery — every member runs one

- **Three models is the floor.** For a team of N, **N − 1 models** is what is expected, with the
  remaining member running the **v1 prompt pass**. A team of six fields five models plus a v1 pass.
- Every member runs one full battery **on their own key**. At 56 runs on the cheap tier that is
  about **US$0.27 each**, so fielding six models costs no more than fielding three.
- **Two conditions, or the comparison is meaningless:**
  1. the models must span **at least two price tiers**, and
  2. **no two members may pick models from the same family**.
- Everyone runs the **identical evaluation set and the identical v2 prompt**. The model name is the
  only thing that may differ between you.

### The v1 pass does not double the battery

v1 runs on **one model only** — the same model you quote its v2 against. To compare prompt versions
you hold the model fixed; to compare models you hold the prompt fixed. Change one thing at a time or
the difference is not attributable to anything.

## Reporting

Pass rate stated **with the model, the prompt version, the run count and the date**, and the
negative cases reported separately — the headline number hides them.

```
<model>, v2 prompt, 40 cases (8 negative) = 56 runs, 48 passed (85.7%);
on the 8 negative cases alone, 19/24 (79.2%)
```

Report §3 is still 350 words. Tables do not count toward the cap, so put **every** model in the
results table and spend the prose on the spread and the two extremes — the cheapest model that met
your bar, the most expensive one that did not earn its price, and where the negative cases separated
them.
