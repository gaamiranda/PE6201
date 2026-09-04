# D6 · The cost-to-serve model

**Owner:** [name] · **Feeds:** report §4 (400 words) · **Criterion:** Reasoning & Justification

> "The part we mark hardest." A cost model that only reports a number says nothing about our design.
> Reuse the Class 5 cost-to-serve notebook. Use measured numbers from D4 and D5, not estimates.

---

## Inputs

| Quantity | Value | Source |
|---|---|---|
| Volume | [8,000 claims / 4,000 referrals] per month | Appendix A |
| Failure cost `F` | [US$7.60 / US$9.17] | [assessor $38/h × 12 min] / [nurse $55/h × 10 min] |
| Measured pass rate `P` | | D4 |
| Median turns `T` | | D7 |
| Tokens in / out per run | | D5 |
| Runs per model | 56 (40 cases: 32 ordinary × 1 trial + 8 negative × 3) | D4 |

## The three layers

```
layer 1 variable         = input·price_in + output·price_out + retrieval + tool fees
layer 2 fallback         = (1 − success_rate) × failure_cost
cost per successful task = layer 1 + layer 2
monthly                  = cost per successful task × volume + layer 3
```

| Layer | Our figure |
|---|---|
| 1 · Per-task variable | |
| 2 · Per-task expected fallback | |
| 3 · Fixed monthly | |
| **Monthly at our volume** | |

**Which world are we in?** We use the **escalate-on-failure** form `(1 − p) × failure_cost`, not
Class 4's `cost / p` retry form, because a wrong outcome here goes to a [claims assessor / triage
nurse], not back into the loop. [one sentence]

## Sensitivity — not a point estimate

| Success rate | Cost per successful task | Monthly |
|---|---|---|
| P − 10pp | | |
| **P (measured)** | | |
| P + 10pp | | |

**Does our conclusion survive the whole range?** [yes/no + one sentence]

## Break-even success rate

```
C = one run on the cheap model (tokens only)          = [ ]
E = one successful task on the expensive model        = [ ]   (its layer 1 + layer 2)
F = one failure                                        = [ ]

failures we can afford  = (E − C) / F  = [ ]
break-even success rate = 1 − (E − C) / F = [ ]
```

**Does our cheap model clear it, or how far short does it fall?** [One sentence with our two
measured numbers in it — the brief calls this "the most useful thing in your report".]

## The cost ledger — four levers, measured before and after

| Lever | Attacks | Before | After | Built in |
|---|---|---|---|---|
| 1 · Tool block size `B` | linear in turns | | | D2(a) |
| 2 · Turn count `T` | the quadratic term | | | D2(c) |
| 3 · Observation size `D` | compounds | | | D2(b) |
| 4 · Success rate | sets layer 2 | | | D4 |

**Which dominated our bill, and how we know:** [...] — a fat tool block is *linear*; a fat
observation *compounds*. Only one of them explodes.

## What the battery actually cost us

The brief's section 7 table was corrected on 1 September — it had been pricing 64 runs by giving
negative cases four trials instead of three. **One member, one full 56-run battery:**

| Tier | Corrected | (was) |
|---|---|---|
| Cheap | **US$0.27** | 0.31 |
| Mid | **US$2.76** | 3.15 |
| Frontier | **US$13.78** | 15.74 |

One member on a frontier model spends **more than the whole course allowance**. If we want a
frontier model in the comparison, run it on the negative cases only and say so in the report.

Because every member runs one model on their own key, fielding five or six models costs the team no
more per person than fielding three — the table is per member, per model.

| Member | Model | Family | Tier | Est. | Actual |
|---|---|---|---|---|---|
| | | | | | |

> Only D5(b) spends money. D3(b), D5(a) and D7 all run on the scripted backend, free. If we find
> ourselves spending live tokens on any of those three, stop.

## Caching / reasoning models

- Prompt caching: [measured with and without, token counts from the API response — or "not used"]
- Reasoning model: [capped to what, cost reported both ways — or "not used, and why"]
