# D6 · The cost-to-serve model

**Owner:** WANG HONGJUN · **Feeds:** report §4 (400 words) · **Criterion:** Reasoning & Justification

*The `usage` block in [`../src/contracts.py`](../src/contracts.py) is where turns, tokens and
cost come from. The calculation is implemented in
[`../cost_model/D6_cost_model.ipynb`](../cost_model/D6_cost_model.ipynb), with machine-readable
output in [`../results/d6_cost_model.json`](../results/d6_cost_model.json). Inputs are audited in
[`../cost_model/D6_input_audit.md`](../cost_model/D6_input_audit.md).*

> "The part we mark hardest." A cost model that only reports a number says nothing about our
> design. We therefore report the three layers, the sensitivity range, the break-even rate, and
> the four cost levers separately.

---

## Inputs

| Quantity | Value | Source |
|---|---:|---|
| Volume | 8,000 claims/month | Appendix A, Problem A |
| Failure cost `F` | US$7.60 | Appendix A: claims assessor at US$38/h x 12 min |
| Runs per model | 76 | D4: 42 cases, 25 ordinary x 1 + 17 negative x 3 |
| Retrieval/tool fees | US$0/run | No separate provider/tool fee recorded |
| Layer 3 fixed monthly | US$500/month | Team deployment assumption, experience-based |
| Monthly per-user limit | US$1,000/user/month | Team deployment assumption, experience-based |

Use the final combined pass rate for D6. Do not use the code-only rate or the decision-only rate.

| Row | Model | Pass rate | Tokens/run in | Tokens/run out | Median turns | Caps fired |
|---|---|---:|---:|---:|---:|---:|
| Scripted baseline | `google/gemini-2.5-flash-lite` | 57/76 = 75.00% | 10,341 | 609 | 5 | 0 |
| Live v2 | `google/gemini-2.5-flash-lite` | 58/76 = 76.32% | 10,462 | 840 | 5 | 0 |
| Live v2 | `mistralai/mistral-medium-3` | 53/76 = 69.74% | 10,457 | 1,003 | 4 | 0 |
| Live v2 | `deepseek/deepseek-chat` | 50/76 = 65.79% | 9,152 | 467 | 4 | 0 |
| Live v2 | `meta-llama/llama-3.3-70b-instruct` | 42/76 = 55.26% | 8,966 | 579 | 5 | 0 |
| Live v2 | `openai/gpt-4o-mini` | 31/76 = 40.79% | 20,226 | 899 | 4 | 12 |
| v1 prompt comparison only | `openai/gpt-4o-mini` | 28/76 = 36.84% | 14,749 | 715 | 4 | 10 |

The `openai/gpt-4o-mini` v1 row is not part of the v2 model-choice comparison. It belongs to the
prompt/descriptor comparison.

## The three layers

```text
layer 1 variable         = input*price_in + output*price_out + retrieval + tool fees
layer 2 fallback         = (1 - success_rate) * failure_cost
cost per successful task = layer 1 + layer 2
monthly                  = cost per successful task * volume + layer 3
```

The live v2 battery gives this ranking:

| Model | Layer 1/run | Layer 2/run | Cost per successful claim | Monthly at 8,000 + layer 3 |
|---|---:|---:|---:|---:|
| `google/gemini-2.5-flash-lite` | US$0.0014 | US$1.8000 | **US$1.8014** | **US$14,911.06** |
| `mistralai/mistral-medium-3` | US$0.0062 | US$2.3000 | US$2.3062 | US$18,949.50 |
| `deepseek/deepseek-chat` | US$0.0028 | US$2.6000 | US$2.6028 | US$21,322.69 |
| `meta-llama/llama-3.3-70b-instruct` | US$0.0011 | US$3.4000 | US$3.4011 | US$27,708.65 |
| `openai/gpt-4o-mini` | US$0.0036 | US$4.5000 | US$4.5036 | US$36,528.58 |

**Which world are we in?** We use the **escalate-on-failure** form
`(1 - p) * failure_cost`, not Class 4's `cost / p` retry form, because a wrong outcome here goes
to a claims assessor rather than back into the loop.

## Sensitivity - not a point estimate

Headline comparison: best cheap-tier live v2 row, `google/gemini-2.5-flash-lite`, against the
mid-tier row, `mistralai/mistral-medium-3`.

| Model | Success rate | Cost per successful claim | Monthly |
|---|---:|---:|---:|
| Gemini, P - 10pp | 66.32% | US$2.5614 | US$20,991.06 |
| Gemini, **P measured** | **76.32%** | **US$1.8014** | **US$14,911.06** |
| Gemini, P + 10pp | 86.32% | US$1.0414 | US$8,831.06 |
| Mistral, P - 10pp | 59.74% | US$3.0662 | US$25,029.50 |
| Mistral, **P measured** | **69.74%** | **US$2.3062** | **US$18,949.50** |
| Mistral, P + 10pp | 79.74% | US$1.5462 | US$12,869.50 |

**Does the conclusion survive the whole range?** No. At the measured rates, Gemini is cheaper, but
the independent +/-10 percentage-point ranges overlap: a weak Gemini point is more expensive than a
strong Mistral point. The measured decision is clear; the sensitivity conclusion is not robust
across the full range.

## Break-even success rate

```text
C = one run on the cheap model (tokens only)          = US$0.0014
E = one successful task on the mid-tier model         = US$2.3062
F = one failure                                       = US$7.60

failures we can afford  = (E - C) / F        = 30.33%
break-even success rate = 1 - (E - C) / F    = 69.67%
```

Gemini's measured rate is **76.32%**, so it clears its break-even rate by **6.64 percentage
points**. At our volume, it is **US$4,038.45/month** and **US$48,461.37/year** cheaper than the
Mistral row under the same layer-3 assumption.

### Supplement: DeepSeek versus Mistral

A separate sensitivity check compares `deepseek/deepseek-chat` with `mistralai/mistral-medium-3`.
The machine-readable result is in
[`../results/d6_deepseek_mistral_sensitivity.json`](../results/d6_deepseek_mistral_sensitivity.json),
with a short write-up in
[`D6-deepseek-mistral-sensitivity.md`](D6-deepseek-mistral-sensitivity.md).

At measured rates, DeepSeek is **50/76 = 65.79%** and Mistral is **53/76 = 69.74%**. DeepSeek's
token layer is cheaper, but its expected fallback cost is higher. It needs **69.69%** success,
effectively **53/76** passes on the 76-trial schedule, to match Mistral's cost.

## The cost ledger - four levers, measured before and after

| Lever | Attacks | Before | After | Built in |
|---|---|---:|---:|---|
| 1 · Tool block size `B` | prompt prefix re-sent every model call | counterfactual fat block: 743 manual tokens, 882,206 input tokens | shipped block: 540 manual tokens, 785,918 input tokens | D2(a) |
| 2 · Turn count `T` | the quadratic history term | 222 turns, 413,519 input tokens | 183 turns, 353,484 input tokens | D2(c) |
| 3 · Observation size `D` | observations re-sent later | manual 265 tokens; `check_coverage` block 32 | manual 540 tokens; `check_coverage` block 307 | D2(b) |
| 4 · Success rate | layer 2 fallback | model-dependent | best live v2: 58/76 = 76.32% | D4/D5 |

Lever 1 is measured as a counterfactual prompt-prefix replay in
[`../evaluation/d6_lever1_run.json`](../evaluation/d6_lever1_run.json). The shipped manual is
replayed against the same 76-trial schedule with two rejected descriptors appended:
`check_required_documents` and `lookup_member`. This isolates tool-block size, not live behaviour.
Removing those descriptors cuts **96,288 input tokens** and **US$0.009640** from the replay, with
turns, model calls, output tokens and decisions unchanged.

Lever 2 was measured with identical calls and identical order. The dependency-rule grouping reduces
turns from **222 to 183** and input tokens from **413,519 to 353,484**, while decisions stay
**40/42** in both arms.

Lever 3 is a safety/interface trade, not a cost win. The v2 manual grows from **265 to 540**
estimated tokens, and the descriptor alone adds **131,216 input tokens** over the 76-trial
schedule. The return shape saves **1,751 input tokens**, but the combined schedule still costs more.

**Which dominated our bill, and how we know:** success rate dominates. At `F = US$7.60` and 8,000
claims/month, one percentage point of pass rate is worth **US$608/month**. That overwhelms the
token-level savings from tool-block cuts, descriptor size, and turn grouping. The token bill is
small; the fallback bill is the system.

## What the battery cost us

The live result summaries do not record actual provider spend. The figures below are token costs
recomputed from committed usage and the verified `PRICES` table, so they are comparable estimates,
not credit-card receipts.

| Run | Model | 76-trial token cost |
|---|---|---:|
| Scripted baseline | `google/gemini-2.5-flash-lite` | US$0.0971 |
| Live v2 | `google/gemini-2.5-flash-lite` | US$0.1050 |
| Live v2 | `mistralai/mistral-medium-3` | US$0.4703 |
| Live v2 | `deepseek/deepseek-chat` | US$0.2156 |
| Live v2 | `meta-llama/llama-3.3-70b-instruct` | US$0.0822 |
| Live v2 | `openai/gpt-4o-mini` | US$0.2716 |
| v1 prompt comparison | `openai/gpt-4o-mini` | US$0.2007 |

Only D5(b) spends live tokens. D3(b), D5(a), and D7 all run on the scripted backend.

## Caps

| Cap | Value | Source |
|---|---:|---|
| Step cap | 12 turns | `src/loop.py`, `Guards` |
| Call cap | 22 model calls | `src/loop.py`, `Guards` |
| Budget ceiling | US$0.016/run | `src/loop.py`, `Guards` |
| Monthly per-user limit | US$1,000/user/month | team experience-based deployment assumption |

The call cap matters because a live run once made 60 model calls while tool-executing turns stayed
low. Counting only turns would miss the bill growth.

## Caching / reasoning models

- Prompt caching: not used and not measured. The baseline uses plain input/output tokens.
- Reasoning model: not used. No reasoning-token adjustment is reported.
