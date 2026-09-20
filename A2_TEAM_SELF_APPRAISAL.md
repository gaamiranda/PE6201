# A2 Team Self-Appraisal

**Team ID:** B-7  **Section:** B  **Problem chosen (A / B):** A

**Members:** Goncalo Miranda · ZHENG YONGJIE · SUN YUCONG · JIN CHENG · NIU TONG · WANG HONGJUN

**Repository URL:** https://github.com/gaamiranda/PE6201  **Date:** 20 September 2026

---

## 1 · Rate your team against Rubric 1

| Criterion | Weight | Excellent (4) | Proficient (3) | Developing (2) | Limited (1) |
|---|---|---|---|---|---|
| Conceptual Understanding | 25% | **✔** | | | |
| Technical Execution | 30% | | **✔** | | |
| Reasoning & Justification | 25% | **✔** | | | |
| Communication & Clarity | 20% | | **✔** | | |

**Why Technical Execution is not Excellent.** The scripted run reproduces from a clean clone with no
key, the caps are instrumented per run, and the live battery ran on five models. But three cases —
`CLM-8888`, `CLM-8894`, `CLM-8952` — fail on every trial of every model, the guardrail checklist
still stands at 9/10, and we shipped a harness with no retry on the live path, which cost SUN YUCONG
61 of 76 trials before we found it. The agent works; it does not work as well as we can describe.

**Why Communication is not Excellent.** Six sections written by six people in two days. The
arguments are sound and every figure traces to a committed file, but the report was assembled at the
end rather than written as one document, and a marker will hear the joins.

## 2 · The one decision you would defend hardest

**Scoring the record separately from the decision, and letting a human judgement overrule a passing
code check.** It cost us a whole extra grading layer and twelve manual verdicts per model, and it is
the reason our headline number looks worse than a decision-only rate would. The evidence is that the
gap is real and large: on the scripted baseline 72 of 76 trials reached the expected decision but
only 57 passed every check, and on `mistralai/mistral-medium-3` the same split is 72 against 53. A
claims system that routes correctly and cannot say why has not done the job, and a decision-only
rate would have hidden that on every model we tested. It also changed what we worked on — the
failures cluster in naming the missing document, not in reading hostile narrative, which was the
opposite of our prediction.

## 3 · The one you are least sure about

**Shipping the v2 six-field descriptor rewrite.** It costs 37.1% more input tokens and 35.3% more
money per battery, and we cannot show it bought accuracy: on the same model and the same 76 trials,
v1 scored 28 and v2 scored 31, a three-trial gap against a standard error of about six, so roughly
half a standard error and not distinguishable from noise. D7's three scripted arms scored
identically, which is not independent evidence either, because replay returns saved responses. We
kept it for inspectability — a size bound on returns, stated failure conditions, an explicit
irreversibility flag — and that is a judgement about auditability, not a measured result. A paired
replicated experiment would settle it and we did not run one.

## 4 · Your headline numbers

| | Value | | Value |
|---|---|---|---|
| Evaluation cases | 42 | Guardrail cases | 10 |
| Negative cases | 17 | Live runs per model (D4) | 76 |
| Pass rate (best model) | 58/76 = 76.32% | Pass rate on negatives only | 37/51 = 72.55% |
| Models in the battery | 5 models, 6 batteries | Median turns per run | 5 |
| The live model YOU ran (D5b) | `openai/gpt-4o-mini`, v2 | Your pass rate on it | 31/76 = 40.79% |
| Turns saved by parallel calls | 222 → 183 = 39 | Cost per successful task | US$1.8014 |
| Monthly cost at problem volume | US$14,911.06 | Break-even success rate | 69.67% |
| Tokens per call — v1 → v2 | 265 → 540 | Pass rate — v1 → v2, same model | 28/76 → 31/76 |

All rates are combined — code check plus human judgement — and all are trial-weighted over the
76-trial schedule (25 ordinary × 1 + 17 negative × 3). Best model is
`google/gemini-2.5-flash-lite`. The v1 → v2 pair is `openai/gpt-4o-mini` on one commit, run by two
members. Cost and break-even are projections at US$7.60 per failure and 8,000 claims a month; no
provider reported actual spend.

## 5 · Contribution

| Member | Owned | Also contributed to |
|---|---|---|
| Goncalo Miranda | The agent loop, the tool layer, the vendor seam, the autonomy gate (D1, D2(a), D2(c)) · report §2 | Coordination, the live-path retry fix and `battery-v2.1`, price correction, D7 failure 1, `gpt-4o-mini` v2 battery |
| ZHENG YONGJIE | D0 · report §1 · assembly of all six sections | `gpt-4o-mini` v1 battery — the controlled prompt arm · fourteen overclaims found by reading D0 against the code |
| SUN YUCONG | Descriptors, the v1→v2 rewrite, the guardrail layer (D2(b), D3) · report §5 | `deepseek-chat` battery · found the missing live-path retry · injection results across models |
| JIN CHENG | The scripted backend and the case loader (D4, D5(a)) · report §6 | `gemini-2.5-flash-lite` battery — the direct replay-versus-live comparison |
| NIU TONG | The evaluation harness and the D5(b) runbook (D4, D5(a)) · report §3 | `llama-3.3-70b` battery · the judgement workflow and its audit trail |
| WANG HONGJUN | The cost model, the ledger and the sensitivity analysis (D6) · report §4 | `mistral-medium-3` battery · re-verified `PRICES` and caught a delisted model the day before the battery |

## 6 · Declaration

- [x] Every member of this team can explain every block of code we submit — what it does, and why it is there.
- [x] The pass rates, token counts, turn counts and costs we report are measurements we ran ourselves. None of them were supplied by an AI assistant.
- [x] Our submitted harness runs end to end on the scripted backend, with no key and no network.
- [x] We kept every fixture record we were given, unedited, and every case in our evaluation set carries a label. `check_my_data.py` passes on our data.
- [x] No part of this submission is drawn from any member's End-of-Course Project, and no part of it will be submitted as part of one.
- [x] This is our own work, and all sources, tools and assistance are attributed.

**Signed on behalf of the team:** ______________________________  **Date:** __________
