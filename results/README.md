# results — every number the report cites

The report argues; this directory tabulates. Nothing in the 2,000 words needs to restate a table
that lives here.

| File | Deliverable | What it holds |
|---|---|---|
| `pass-rates.md` | D4, D5 | Pass rate per policy and per model, with trial count, model id and date |
| `turn-distribution.md` | D7 | Median, worst case, and how many runs hit the step cap |
| `sequential-vs-parallel.md` | D2(c) | Turns, tokens and cost both ways, plus the pass rate that did not move |
| `descriptor-v1-v2.md` | D2(b) | Tokens per call, pass rate, guardrail cases, for each version |
| `model-battery.md` | D5 | The three models side by side — and where they diverged on the negative cases |
| `cost-model.md` | D6 | Three layers, four levers, sensitivity table, break-even |
| `decisions.jsonl` | D1 | The gated action's output — one structured record per decision |

Every number here is one **we ran**, not one a model produced for us.
