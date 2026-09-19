# D6 input audit

Date checked: 2026-09-19

Purpose: lock the repository inputs for D6 before running the cost model. This file records what
will be read from the repository, what each input is used for, and what still needs to be labelled
as an assumption rather than a measurement.

## Assignment scope

- Problem: A, health-insurance claim first response.
- Volume: 8,000 claims/month.
- Failure cost `F`: US$7.60 per failed claim.
- Failure-cost source: Appendix A, claims assessor at US$38/hour for 12 minutes.
- Retrieval/tool fees: none recorded separately in the repository; use US$0 unless a later source is
  added.
- Layer 3 fixed monthly cost: US$500/month, set by the team as an experience-based deployment
  assumption rather than a measured repository cost.

## Price table

Source: `src/backends.py`, `PRICES`, verified in that file against OpenRouter's model feed on
2026-09-17.

| Model id | Input US$/M | Output US$/M | D6 use |
|---|---:|---:|---|
| `openai/gpt-4o-mini` | 0.15 | 0.60 | live battery, cheap tier |
| `google/gemini-2.5-flash-lite` | 0.10 | 0.40 | scripted baseline and live battery, cheap tier |
| `mistralai/mistral-medium-3` | 0.40 | 2.00 | live battery, mid tier |
| `meta-llama/llama-3.3-70b-instruct` | 0.10 | 0.32 | live battery, cheap tier |
| `deepseek/deepseek-chat` | 0.2574 | 1.0287 | live battery; price moved during freeze check |
| `anthropic/claude-haiku-4.5` | 1.00 | 5.00 | priced but not fielded |
| `scripted` | 0.00 | 0.00 | replay backend only, no API spend |

## Final run summaries

Source: `results/evaluations/*final.summary.json`. All rows below have `combined_score_status =
complete`, `code_checked_trial_count = 76`, and `missing_judgement_trial_count = 0`.

| Run | Model | Pass rate | Tokens in | Tokens out | Median turns | Caps fired | D6 use |
|---|---|---:|---:|---:|---:|---:|---|
| `eval-scripted-v2-final.summary.json` | `google/gemini-2.5-flash-lite` | 57/76 = 75.00% | 785,906 | 46,280 | 5.0 | 0 | D5(a) scripted baseline |
| `eval-openrouter-google-gemini-2.5-flash-lite-v2-jincheng-gemini25flashlite-final.summary.json` | `google/gemini-2.5-flash-lite` | 58/76 = 76.32% | 795,150 | 63,818 | 5.0 | 0 | live battery, v2 prompt |
| `eval-openrouter-mistralai-mistral-medium-3-v2-wang-mistral-medium-3-final.summary.json` | `mistralai/mistral-medium-3` | 53/76 = 69.74% | 794,727 | 76,201 | 4.0 | 0 | live battery, v2 prompt |
| `eval-openrouter-deepseek-deepseek-chat-v2-sun-deepseek-chat-v21-rerun2-final.summary.json` | `deepseek/deepseek-chat` | 50/76 = 65.79% | 695,532 | 35,513 | 4.0 | 0 | live battery, v2 prompt |
| `eval-openrouter-meta-llama-llama-3.3-70b-instruct-v2-niu-tong-final.summary.json` | `meta-llama/llama-3.3-70b-instruct` | 42/76 = 55.26% | 681,411 | 43,990 | 5.0 | 0 | live battery, v2 prompt |
| `eval-openrouter-openai-gpt-4o-mini-v2-goncalo-gpt4omini-final.summary.json` | `openai/gpt-4o-mini` | 31/76 = 40.79% | 1,537,210 | 68,289 | 4.0 | 12 | live battery, v2 prompt |
| `eval-openrouter-openai-gpt-4o-mini-v1-zheng-v1-final.summary.json` | `openai/gpt-4o-mini` | 28/76 = 36.84% | 1,120,947 | 54,342 | 4.0 | 10 | v1 prompt comparison only |

Do not mix the `openai/gpt-4o-mini` v1 row into the v2 model battery comparison. It is evidence
for the prompt/descriptor comparison, not a model-choice row under the same prompt.

## D6 lever inputs

### Lever 1: tool block size `B`

Source: `docs/D2-tool-layer.md`.

- Two tools were refused at design time: `check_required_documents(procedure_code)` and
  `lookup_member(member_id)`.
- Measurement: `evaluation/d6_lever1_run.json`, reproducible via
  `python3 evaluation/measure_d6_lever1.py`.
- Scope: counterfactual prompt-prefix replay. It measures the token/cost effect of carrying the
  two rejected tool descriptors in the tool block. It does not re-measure live model behaviour.
- Shipped tool block: 540 estimated manual tokens; 785,918 input tokens; US$0.097096 projected
  cost over the 76-trial schedule.
- Counterfactual fat tool block: 743 estimated manual tokens; 882,206 input tokens; US$0.106736
  projected cost over the same schedule.
- Difference: +203 manual tokens, +96,288 input tokens, +US$0.009640, with decisions unchanged.

### Lever 2: turn count `T`

Sources: `evaluation/d2c_run.json`, reproducible via `python3 evaluation/measure_d2c.py`.

| Arm | Median turns | Total turns | Input tokens | Output tokens | Cost | Decisions |
|---|---:|---:|---:|---:|---:|---:|
| Sequential | 5 | 222 | 413,515 | 15,012 | US$0.071031 | 40/42 |
| As recorded | 5 | 216 | 404,188 | 14,974 | US$0.069609 | 40/42 |
| By dependency rule | 4 | 183 | 353,481 | 14,746 | US$0.061867 | 40/42 |

Measured saving versus sequential:

- As recorded: 2.7% turns, 2.3% input tokens, 2.0% cost.
- By dependency rule: 17.6% turns, 14.5% input tokens, 12.9% cost.
- Decisions changed: 0.

### Lever 3: observation size `D`

Source: `docs/D2-tool-layer.md`.

- Tool manual: 265 -> 540 estimated tokens.
- `check_coverage` descriptor block: 32 -> 307 tokens.
- Descriptor alone: +131,216 input tokens over the 76-trial schedule.
- Return shape alone: -1,751 input tokens.
- The combined descriptor/shape schedule moved from US$0.084157 to US$0.097096.
- This is a safety/interface improvement, not a cost reduction.

### Lever 4: success rate

Source: `results/evaluations/*final.summary.json`.

- Use final combined pass rate, not code-only or decision-only rates.
- For the scripted baseline: 57/76 = 75.00%.
- For live v2 battery rows, use the table in "Final run summaries" above.
- Dominance check for Step 2: at F = US$7.60, success rate is expected to dominate token price.

## Caps

Source: `src/loop.py`, `Guards`.

| Cap | Value | Status |
|---|---:|---|
| `step_cap` | 12 turns | measured and configured |
| `call_cap` | 22 model calls | measured and configured |
| `budget_ceiling_usd` | US$0.016/run | measured and configured |
| monthly per-user limit | US$1,000/user/month | experience-based deployment assumption |

## Report files to update later

- `evaluation/d6_cost_model.ipynb`: Step 2 will make it read these inputs and calculate the D6
  outputs.
- `docs/D6-cost-model.md`: Step 3 will fill the working D6 evidence document.
- `docs/report/S4-cost-to-serve.md`: Step 4 should create this report section, because
  `docs/report/README.md` lists it but the file does not exist yet.

## Remaining decisions before calculation

The repository has enough measured data to calculate D6. Two choices/assumptions must be explicit
when writing the result:

1. Which live battery comparison to headline. The repository supports all v2 live models. A natural
   D6 comparison is the best cheap-tier v2 result against the mid-tier Mistral row, but Step 2 should
   calculate all rows before choosing the report headline.
2. How to state layer 3 and monthly per-user limit. The team has set `FIXED_MONTHLY_USD = 500.0`
   and `MONTHLY_LIMIT_USD_PER_USER = 1_000` as experience-based deployment assumptions. Label them
   that way in D6 rather than presenting them as measured costs.
