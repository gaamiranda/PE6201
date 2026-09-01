# harness — the evaluation runner

D4 and D5. This is the instrument that makes the whole submission credible.

## Requirements it must satisfy

- **`BACKEND = "scripted"` is the default.** Deterministic canned responses, no network, no key, so
  a marker can clone and reproduce every number at zero cost. If the harness does not run this way,
  Technical Execution is **capped**.
- **Isolation** — each case starts from a clean state. No case may depend on a previous one running.
- **Multi-trial** — 3 trials per case by default.
- **Mixed graders** — automatic (L1) where an automatic check is honest, judgement (L2: LLM-as-judge
  against a rubric, or a named human) where it is not.
- **Outcome-graded**, and a run that reaches the right outcome by the *wrong trigger* is not a pass.

## Instrumentation — per run, every run

Without this a loop failure is invisible: it raises no exception, it just costs more.

```
turns used · tokens in · tokens out · estimated cost · whether a cap fired · tools called, in order
```

## What it reports

Pass rate stated **with the model, the policy, the trial count and the date** — and the negative
cases reported separately, because the headline number hides them.

```
careful policy, <model>, 40 cases x 3 trials = 120 trials,
103 passed (85.8%); on the 8 negative cases alone, 19/24 (79.2%)
```

Beware the substring check that passes for the wrong reason. Check the thing you care about, not a
string that usually accompanies it.
