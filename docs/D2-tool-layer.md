# D2 · The tool layer

**Owners:** Goncalo Miranda · ZHENG YONGJIE (D2a, D2c) · SUN YUCONG (D2b) · **Feeds:** report §2 (450 words) · **Criteria:** Technical Execution + Reasoning

*Signatures are frozen in [`../src/contracts.py`](../src/contracts.py). Deadlines: [`../PLAN.md`](../PLAN.md).*

> The tool descriptions and signatures are the entire manual the model gets. It cannot ask a
> colleague, hover a tooltip, read our source, or try it in staging.

> **The tool names in Appendix A are suggestions, not an interface to implement** (change notice,
> 1 Sep). Rename, re-argument, merge, split or add tools as our design requires — the reason is
> D2(b): you cannot meaningfully write a six-field descriptor for a signature somebody else fixed.
> **What is not negotiable is the routing rule and the gated action**, because the answer key is
> written against them.

---

## D2(a) · The tool set — chosen, not collected

**Method.** We started from the six tools Appendix A calls the minimum set, walked all 15 shipped
claims against the routing table by hand, and recorded where those six could not reach a decision.
Everything below is an *observed* failure against `expected_outcomes_A.json`, not an imagined one.

### What the minimum set could not decide

| Case | Family | Expected | Why the six tools cannot reach it |
|---|---|---|---|
| `CLM-8901` | `required_document_absent` | `request_document` | 45378 requires an itemised bill; the claim attaches **none**. `required_documents.json` is unreachable — no tool opens it. |
| `CLM-8933` | `duplicate_of_decided_claim` | `escalate` / `duplicate_claim` | Resubmission of `CLM-8710` under a new id. `decided_claims.json` is unreachable — no tool opens it. |
| `CLM-8850` | `single_line_short_run` | `approve_in_principle` | Reaches the right outcome, but `must_record` requires stating it is **not** a duplicate of `CLM-8702`. Unprovable without the history. |
| `CLM-8960` | `four_line_long_run` | `approve_in_principle` | Same — `must_record` requires the comparison against `CLM-8726`, which differs only on the lines. |

Two of fifteen are undecidable and two more cannot produce a full-marks record. That is the
failure that licenses a change to the tool set.

### Before adding a tool, we tried not adding one

The four moves, in the brief's order of preference:

**1 · Widen an existing tool's parameters** — *not used.* Neither gap is a missing argument.

**2 · Return more from one call** — **used, and it removed a tool before it shipped.**
`required_documents.json` is keyed on `procedure_code`. `check_coverage(policy_id, procedure_code)`
already holds that key and already returns `requires_preauth` for the same reason. So
`document_required` joins the same return shape rather than becoming
`check_required_documents(procedure_code)`. **One fewer descriptor in the prompt prefix, zero extra
calls, and `CLM-8901` becomes decidable.**

**3 · Move the step out of the loop into ordinary code** — *tried, and rejected on purpose.*
The duplicate check is a pure function of what `get_claim` already returned — member, hospital,
date, lines — so it could run as a pre-filter before the agent starts. We kept it in the loop
anyway, for two reasons. The routing table makes `duplicate_claim` an **escalation trigger**, and
the record must carry the evidence trail that produced it; a pre-filter escalates claims the agent
never reasoned about, and the `evidence` list would not show the check. It also costs nothing to
keep: the call joins the turn-2 fan-out and adds **no turn** (see D2(c)).

**4 · Add the tool** — once, for the duplicate check. Observed failure: `CLM-8933`.

### The set we ship

| # | Tool | 1 · Does a task fail without it? | 2 · Confusable? | 3 · Cost when never called | Verdict |
|---|---|---|---|---|---|
| 1 | `get_claim(claim_id)` | Yes — nothing else resolves a claim id, and every other tool needs a field it returns | No — the only entry point | Never uncalled; it is turn 1 | **keep** |
| 2 | `lookup_policy(member_id)` | Yes — the member → policy hop, and the only source of status, dates, headroom and exclusions. Three of the five escalation triggers come out of this one call | No | Never uncalled | **keep** |
| 3 | `check_coverage(policy_id, procedure_code)` | Yes — decides each line, and its `requires_preauth` and `document_required` fields decide whether the run continues | No — the only per-line tool | Fires once per line, never idle | **keep** (widened) |
| 4 | `get_preauthorisation(member_id, procedure_code, date_of_service)` | Yes — `CLM-8888` and `CLM-8894` are undecidable without it | No | Idle on 10 of 15 claims, but its descriptor is ~60 tokens re-sent every turn ≈ 240 tokens/run at T=4 | **keep** |
| 5 | `get_hospital_status(hospital_id)` | **No outcome fails without it** — panel status never changes a decision in the shipped set | No | Same prefix cost, called every run | **keep, with a caveat →** |
| 6 | `check_claim_history(member_id, hospital_id, date_of_service, lines)` | Yes — `CLM-8933`, and the `must_record` on `CLM-8850` / `CLM-8960` | No | Fires once per run | **added** |
| 7 | `issue_decision_letter(record)` | Yes — it is the deliverable. One log record, not a letter | No | The only write; one gate covers the whole agent | **keep, gated** |

**The caveat on `get_hospital_status`.** It is the tool in this set that most resembles Class 4's
`search_notes`: no outcome in the shipped 15 turns on it. It survives only because `CLM-8874`'s
`must_record` demands `H-330` be recorded as non-panel — the answer key's own note says *"Non-panel
is decidable. It changes what the record must SAY, not what the decision is."* We keep it because
the record requirement is part of the specification, and we say here that it is the first tool we
would cut in production.

### Tools we did not ship

| Tool | Why not | Evidence |
|---|---|---|
| `check_required_documents(procedure_code)` | Absorbed into `check_coverage`'s return by move 2 — same key, same call site | Removes one descriptor from the prompt prefix at no cost in calls or turns |
| `lookup_member(member_id)` | **The trap, and we refused it.** It fails question 1 (nothing needs it — `lookup_policy` does the hop) and question 2 (directly confusable with `lookup_policy`), and it is actively dangerous: it would return `join_date`, which *looks* like a coverage date and is not | `CLM-8917` is live-policy-wrong-date. The data dictionary says it outright: *"join_date — Not a coverage date; the policy's own dates govern."* A model handed both dates in one observation has been given a landmine, not a fact |

`lookup_member` is the tool that would have come out looking like `search_notes`. Not shipping it
is a design decision, and `CLM-8917` is the case that would have paid for it.

### Signature choices that carry the poka-yoke (feeds D2(b))

Two of the signatures above make a class of error *unrepresentable* rather than discouraged.
Detail belongs in D2(b), but the decisions are made here because they are signature decisions:

| Before | After | What it makes impossible |
|---|---|---|
| `get_preauthorisation(member_id, procedure_code)` | `get_preauthorisation(member_id, procedure_code, date_of_service)` — required, not optional | Finding an approval and never testing the window. `CLM-8894` is exactly this: `PA-5640` **exists** and expired 2026-05-31. The key calls it *"the case teams most often get wrong."* |
| a duplicate check on any subset of the facts | `check_claim_history(member_id, hospital_id, date_of_service, lines)` — all four required | A three-fact match. The history ships **three deliberate near-misses**, each differing on one fact; every shortcut wrongly escalates a good claim |

A third falls out of the shape already in Appendix A: `check_coverage` takes a **`policy_id`**, not
a `member_id`, so the member → policy hop has to happen once, in `lookup_policy`, and appears in the
evidence trail as its own call. Note the difference from the two rows above, which are genuine
impossibilities — a required argument that cannot be omitted. This one is weaker and we state it as
such: `check_coverage` checks that the policy id *exists*, not that this claimant holds it. What it
buys is a visible hop, not an unrepresentable pairing.

---

## D2(b) · Descriptor contracts — six fields, no exceptions

One block per tool. Copy this shape:

```
NAME + SIGNATURE   tool_name(arg: type, arg2: Literal["A","B"]) -> ReturnType
WHAT               One line: what this answers that nothing else answers.
INPUT              Each argument, its type, and what a bad value does.
RETURNS            The shape, and a SIZE BOUND. "At most 3 records, 40 tokens each."
FAILS WHEN         The named conditions under which it returns nothing or errors.
IRREVERSIBLE?      Yes / No. If yes, name the gate that covers it.
```

### Poka-yoke moves (at least two)

State what each makes **impossible** — not what it discourages.

| Before | After | What it makes impossible |
|---|---|---|
| `get_preauthorisation(member_id, procedure_code)` | `get_preauthorisation(member_id, procedure_code, date_of_service)` | Returning "approval found" without testing whether it applies on the service date. |
| a duplicate check on any subset of facts | `check_claim_history(member_id, hospital_id, date_of_service, lines)` | A three-fact duplicate match. All four match facts must be supplied together. |
| `check_coverage(member_id, procedure_code)` or a free policy lookup inside the model's reasoning | `check_coverage(policy_id, procedure_code)` | **Weaker than the rows above, deliberately.** Not an impossibility: it forces the member → policy hop into `lookup_policy`, where the date test lives, and makes it visible in the trace. The tool validates that the policy id exists, not that the claimant holds it. |
| separate `covered`, `requires_preauth`, and `document_required` flags | `coverage.status` plus `needed_next[]`, empty when `coverage.status == "not_covered"` | The tool observation cannot say a line is excluded and also ask the agent to chase pre-authorisation or documents for that same refused line. |

### The measured rewrite

One tool, v1 vs v2 of its descriptor and return shape.

| | Manual size, re-sent on every model call | Eval pass rate | Guardrail cases passed |
|---|---|---|---|
| v1 | Whole manual 265 estimated tokens; `check_coverage` block **32** | Not measured here; scripted replay is keyed only by case and turn, so v1/v2 replay the same model replies. | Not measured here for the same reason. |
| v2 | Whole manual 540 estimated tokens; `check_coverage` block **307** | Not measured here; token delta only. | Not measured here; token delta only. |

Both block figures were re-measured after the signature de-annotation below, which took ~8 tokens
out of every block in both manuals. What the `+275` costs across a whole schedule is measured in
[`D7-failures.md` §Failure 2.3](D7-failures.md), where three arms separate the descriptor from the
return shape that shipped alongside it: **the descriptor alone is +131,216 input tokens over the
76-trial schedule**, the shape alone is −1,751, and the two together take the schedule from
US$0.084157 to US$0.097096. A 275-token block, re-sent on every model call, is 15% of what the
whole battery costs.

**v1 descriptor in `tools.DESCRIPTORS_V1`, as `tool_manual("v1")` renders it:**

```
check_coverage(policy_id, procedure_code)
Checks whether a procedure is covered by a policy and says if anything else is needed.
```

The signature line is rendered by `tool_manual`, not stored, so the de-annotation below applies to
**both** versions. That is deliberate: v1 and v2 must differ in the descriptor prose and nothing
else, or the comparison measures our rendering bug instead of SUN YUCONG's rewrite.

**v2 descriptor in the `check_coverage` docstring:** six fields: name/signature, what, input,
returns with a size bound, fails when, irreversible. `loop.tool_manual("v1")` and
`loop.tool_manual("v2")` both build seven blocks and differ in exactly one block, the
`check_coverage` block. The whole-manual token delta is `+275` estimated tokens (`265 -> 540`).

### The defect the rewrite uncovered — and the poka-yoke that fixed it

Rewriting the descriptor meant reading the manual the model actually receives, and that exposed a
defect in how `tool_manual()` rendered every tool, not just the one being rewritten.

The manual was built with `str(inspect.signature(fn))`, which renders Python's annotation syntax:

```
get_claim(claim_id: 'str') -> 'Claim'
```

The model copied that **colon** into its calls — `get_claim(claim_id: 'CLM-9034')`. `_parse_call`
reads arguments with `ast.literal_eval`, so a colon is a syntax error. The model was told "invalid
syntax", could not read our source to learn why, and retried verbatim.

| Recording | Replies carrying a colon-style call |
|---|---|
| Before the v2 rewrite | 35 / 388 — **9.0%** |
| After the v2 rewrite | 48 / 378 — **12.7%** |
| After rendering parameter names only | **0 / 426 — 0.0%** |

The v2 descriptor made it *worse*, because its `NAME + SIGNATURE` line repeated the same annotation
style and reinforced the pattern. On `CLM-9034` the model never escaped: 18 model calls, 17
unproductive rounds, **zero tools executed**, and an escalation reached without ever having read the
claim.

The fix is one line — render `get_claim(claim_id)` — and it is the D2(b) thesis applied to our own
prompt. The manual is paid on every call of every run, so a defect in how it renders is paid the
same way. The alternative, a sentence saying "use `=` not `:`", would have cost tokens forever and
could still be missed. **Changing what the model is shown costs nothing per call; telling it what to
do costs something every call.**

What the fix bought, measured on the harness:

| | Code check | Negative code check | Decision |
|---|---|---|---|
| Annotated manual | 54/76 (71.1%) | 30/51 (58.8%) | 36/42 |
| Parameter names only | 61/76 (80.3%) | **39/51 (76.5%)** | 36/42 |
| + JSON literals accepted, and the prompt saying which outcomes have no tool | **63/76 (82.9%)** | **39/51 (76.5%)** | **40/42** |

Record *quality* rose nine points while the decision rate held. It also stopped masking a real
problem: with the syntax loop gone, five document cases became visibly deadlocked rather than dying
early for the wrong reason, which exposed two further defects of the same kind — our prompt asking
for "a JSON decision record" while the Action parser rejected JSON's `null`, and the prompt never
saying that `escalate` and `request_document` have no tool to call. Fixing those took the set to
**63/76 code, 40/42 decisions, no caps fired anywhere, and a projected 76-trial cost of US$0.097**
— down from US$0.367 at the worst point. See `docs/D3-guardrails.md`.

**The pattern across all three defects is the same, and it is this document's thesis.** Every one
was a place where what we *showed* the model contradicted what we *accepted* from it. None was
fixed by telling the model to try harder, and each fix was paid once rather than on every call.

**Verdict:** v2 is longer, so it is not a cost win. It is a safety/interface win: the return
shape now exposes a single coverage result and a bounded `needed_next` list. That makes an
internally contradictory observation impossible for excluded lines: the tool cannot return
`not_covered` and simultaneously return branch flags telling the agent to pursue paperwork for
that refused line. The pass-rate comparison must be a later live run, not the scripted backend,
because the scripted backend replays the same recorded replies for either prompt version.

---

## D2(c) · Calling more than one tool in a turn

> **The brief's worked examples are examples, not the prescribed answer** (change notice, 1 Sep).
> If we parallelise less, group calls differently, or keep a call on its own so we can read its
> result first, that is not a mistake. **D2(c) marks the reasoning, not the number.** What is
> required: a stated dependency rule, the measurement taken both ways, and evidence that correctness
> did not change.
>
> For reference, the corrected figures in the brief: Problem A, 8 sequential turns → 4,
> 20,800 → 9,600 tokens (54%). Problem B, referral REF-5602, 6 calls, 4 turns, 13,200 → 8,400 (36%)
> — deliberately smaller, because B's work is a chain and a chain cannot be shortened by running
> things at the same time.

### The dependency rule

> **Two calls may share a turn only when neither consumes the other's output.**

Signatures and the machine-readable version are in [`../src/contracts.py`](../src/contracts.py)
(`DEPENDS_ON`).

| Turn | Calls | Why they can (or cannot) share it |
|---|---|---|
| 1 | `get_claim` | Alone. Every other tool reads a field it returns. |
| 2 | `lookup_policy` ‖ `get_hospital_status` ‖ `check_claim_history` | All three derive from the claim row and from nothing else. Adding the duplicate check here costs **no turn**. |
| 3 | `check_coverage` × *n* lines, together | Needs `policy_id`, which turn 2 produced. The *n* line checks are independent of each other, so *n* calls cost one turn — this is where the saving is. |
| 4 | `get_preauthorisation` | Cannot join turn 3: which line needs one is unknown until coverage answers. |
| 5 | `issue_decision_letter` | Gated, and a turn like any other — gated, not free. |

**Five turns, where the brief's worked example shows four — and this is a deliberate trade, not
a miss.** The brief folds `check_coverage` into turn 2 beside `lookup_policy`. That grouping is
only reachable if `check_coverage` does the member → policy hop itself. We took a **`policy_id`**
instead, because it forces that hop into its own named call where a reader of the evidence trail
can see which policy was used — and it costs exactly one turn.

So the choice is a poka-yoke against a turn, and we are measuring both rather than asserting one:

| | Turns | The safety property |
|---|---|---|
| `check_coverage(policy_id, procedure_code)` — **shipped** | 5 | The hop happens once, in `lookup_policy`, and is auditable from the trace |
| `check_coverage(member_id, procedure_code)` | 4 | The hop is repeated inside the tool and is unverifiable from the trace |

The change notice is explicit that this is ours to decide: *"Where the parallel boundary falls is
your design judgement, and D2(c) marks the reasoning, not the number… A team that parallelised
less than we did and explained why is on stronger ground than one that copied this page."*

### The honest limits — predicted, before measuring

The brief asks us to find these. We wrote these two down **before** running the measurement, and
kept them here unedited so the prediction can be compared with the result — see *The two honest
limits* below, where one of them turns out to be worth 45 tokens rather than the cost regression
we expected:

1. **Early exits pay for work they never use.** `CLM-8910` (lapsed policy) and `CLM-8925` (over the
   annual limit) both escalate the moment `lookup_policy` returns — the answer key's note on
   `CLM-8925` says *"the early exit is the correct behaviour"*, and the brief's own record shows it
   finishing in two turns. But turn 2 has already paid for `get_hospital_status` and
   `check_claim_history`. On those cases parallelising is a **cost regression**, and we report the
   figure rather than the headline.
2. **It removes a decision point.** Firing the three turn-2 lookups together means the model never
   sees `status: lapsed` before deciding whether to ask about the hospital. Sequentially it would
   have skipped both.

### The measurement

Reproduce with `python3 evaluation/measure_d2c.py` — scripted backend, no API key, US$0.00,
deterministic. Output in `evaluation/d2c_run.json`.

**How it was measured, because the obvious way does not work.** `Guards(parallel=False)` takes the
first call of a reply and discards the rest (`batch = calls if g.parallel else calls[:1]`).
Replaying the committed transcript that way runs off the end of the recording — the reply for turn 7
assumes the calls dropped from turn 3 already happened — and the run dies with
`BackendError: no recorded response`. That crash is D2(c)'s thesis arriving as an exception:
sequential execution needs more round trips than parallel, and a recording made in parallel does not
contain them.

So all three arms below replay the **same tool calls, in the same order, from the same recording**,
and differ only in how many calls may share one model round trip. Every observation is real, the
tools genuinely execute, and the message history is rebuilt and re-sent exactly as the loop sends
it. Every synthesised reply carries one fixed `Thought:` string — the control, because the model's
own thoughts vary in length, land in the history, and would otherwise leak prose length into a
measurement of grouping. The driver is checked against an ordinary scripted run before anything
else runs: replaying the recording verbatim must reproduce 473,596 input tokens and 40/42, and it does.

**All 42 cases are measured.** An earlier recording had three that never reached a `Final:` and had
to be excluded, because a synthesised script with no terminating reply spins to the step cap and the
table measures the cap rather than the grouping. Those deadlocks were prompt defects, not model
limits, and they are fixed — `evaluation/measure_d2c.py` still prints the exclusion list, and it is
now empty.

| | Turns (median) | Turns (total) | Input tokens | Output tokens | Cost | Pass rate |
|---|---|---|---|---|---|---|
| **Sequential** — one call per turn | 5 | 222 | 413,515 | 15,012 | US$0.07103 | **40/42** |
| **As recorded** — the grouping the model chose | 5 | 216 | 404,188 | 14,974 | US$0.06961 | **40/42** |
| **By rule** — the largest batches `DEPENDS_ON` permits | **4** | **183** | **353,481** | 14,746 | **US$0.06187** | **40/42** |

| vs sequential | Turns | Input tokens | Cost |
|---|---|---|---|
| As recorded | −2.7% | −2.3% | −2.0% |
| By rule | −17.6% | −14.5% | −12.9% |

**Correctness did not move: 40/42 in all three arms, and not one case decided differently** —
neither between sequential and as-recorded, nor between as-recorded and by-rule. That is the result
that matters. Parallelism is a scheduling choice, and a scheduling choice that changed an answer
would be a bug.

Note that the saving is almost entirely on the **input** side: output tokens barely move
(15,012 → 14,746), because the same Action text is emitted either way, merely distributed over
fewer replies. What parallelising buys is re-sending the system prompt and the accumulated history
fewer times. That is also why the saving is bounded by how long the prompt is, not by how many
tools exist.

### The gap between "as recorded" and "by rule" is the real finding

Our loop has supported multi-call turns from the start. **The model barely uses them.** Across the
whole recording:

| Calls in one action-turn | Turns | Share |
|---|---|---|
| 1 | 215 | **97.7%** |
| 2 | 4 | 1.8% |
| 4 | 1 | 0.5% |


**Only 4 of 42 cases ever used a multi-call turn.** And the group this document predicted —
`lookup_policy ‖ get_hospital_status ‖ check_claim_history` on turn 2 — **never occurs once**. What
the model actually grouped was:

```
3 x  check_coverage | get_preauthorisation
1 x  check_claim_history | issue_decision_letter
1 x  check_claim_history | check_coverage | get_hospital_status | get_preauthorisation
```

Three of those pair `check_coverage` with `get_preauthorisation`, which `DEPENDS_ON` says is the
one grouping that is *not* allowed: which line needs a pre-authorisation is unknown until
coverage answers. The model is not parallelising, it is **speculating** — issuing the pre-auth
lookup before knowing whether it is needed. It gets away with it because the arguments
(`member_id`, `procedure_code`, `date_of_service`) all come from the claim row, so the call is
*expressible* even though it is logically premature. The dependency is a reasoning dependency, not
a data dependency, and a signature cannot enforce it.

So the honest reading of the three-arm table: **of the 17.6% of turns the dependency rule makes
available, the model captured 2.7% and left 15 points on the table.** That is a prompt and model
finding, not a loop limitation — and it is a concrete thing for the D5(b) battery to look for,
because "does this model use multi-call turns" is exactly the kind of divergence six models should
be expected to differ on.

### The two honest limits

**1 · Where a parallel call raises cost, and why it barely does.** The prediction above was that
`CLM-8910` (lapsed policy) and `CLM-8925` (over the annual limit) would be cost regressions: both
escalate the moment `lookup_policy` returns, so a speculative turn-2 group has already paid for
`get_hospital_status` and `check_claim_history`.

Measured, the regression is **45 input tokens** on each — 17 for the hospital status, 28 for the
claim history. On `CLM-8910` that is 0.5% of the run. It did not appear in the table at all
(`by rule` raised input tokens on **zero** of 42 cases) for a reason worth stating plainly: the
by-rule arm regroups calls the model actually made, and on those two cases the model exited before
making them. A genuinely parallel-first agent would pay the 45 tokens; ours never got the chance.

That the penalty is 45 tokens rather than 450 is not luck. It is D2(a)'s bounded returns — *"4
fields, ~30 tokens, never a list"* — cashing out. **Speculative parallelism is cheap exactly when
tool returns are bounded**, which is the same design decision, measured from the other side.

**2 · It removes a decision point.** Firing the three turn-2 lookups together means the model never
sees `status: lapsed` before deciding whether to ask about the hospital. Sequentially it would have
skipped both calls. This cannot be priced in tokens — the cost is that a cheap early exit stops
being available, and the 45 tokens above are what that costs when it happens.

**Why our saving is 14.5% where the brief's example shows 54%.** The brief's figure comes from a
claim whose `check_coverage` calls fan out across several lines — that fan-out is where the saving
lives. On our set **27 of 42 claims have a single line**, 6 have two, 8 have three and 1 has four.
A one-line claim has nothing to fan out, so two thirds of our set cannot benefit from the move that
produces the brief's number. We are reporting the figure our data supports rather than the one the
example shows.

### What this measurement cannot tell us

It measures what the **identical work** costs under three scheduling strategies. It does not measure
whether a live model *instructed* to work sequentially would choose the same calls — it might take
a different path, or fewer. That needs a second live recording under a sequential prompt, which is
a battery question, not a replay question. Stated here because the distinction is the difference
between a measurement and an assumption.
