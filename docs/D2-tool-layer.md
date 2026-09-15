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
a `member_id`, so a coverage check against a policy the member does not hold cannot be expressed.

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
| `check_coverage(member_id, procedure_code)` or a free policy lookup inside the model's reasoning | `check_coverage(policy_id, procedure_code)` | Checking coverage against a policy the member does not hold. The caller must use the policy id returned by `lookup_policy`. |
| separate `covered`, `requires_preauth`, and `document_required` flags | `coverage.status` plus `needed_next[]`, empty when `coverage.status == "not_covered"` | The tool observation cannot say a line is excluded and also ask the agent to chase pre-authorisation or documents for that same refused line. |

### The measured rewrite

One tool, v1 vs v2 of its descriptor and return shape.

| | Tokens returned per call | Eval pass rate | Guardrail cases passed |
|---|---|---|---|
| v1 | Manual: 325 estimated tokens; check_coverage block: 40 estimated tokens | Not measured here; scripted replay is keyed only by case and turn, so v1/v2 would replay the same model replies. | Not measured here for the same reason. |
| v2 | Manual: 602 estimated tokens; check_coverage block: 318 estimated tokens | Not measured here; token delta only. | Not measured here; token delta only. |

**v1 descriptor in `tools.DESCRIPTORS_V1`:**

```
check_coverage(policy_id: 'str', procedure_code: 'str') -> 'CoverageResult'
Checks whether a procedure is covered by a policy and says if anything else is needed.
```

**v2 descriptor in the `check_coverage` docstring:** six fields: name/signature, what, input,
returns with a size bound, fails when, irreversible. `loop.tool_manual("v1")` and
`loop.tool_manual("v2")` both build seven blocks and differ in exactly one block, the
`check_coverage` block. The whole-manual token delta is `+277` estimated tokens (`325 -> 602`).

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
instead, because it makes a coverage check against a policy the member does not hold
*unrepresentable* — and it costs exactly one turn.

So the choice is a poka-yoke against a turn, and we are measuring both rather than asserting one:

| | Turns | The safety property |
|---|---|---|
| `check_coverage(policy_id, procedure_code)` — **shipped** | 5 | Wrong-policy coverage check cannot be expressed |
| `check_coverage(member_id, procedure_code)` | 4 | The hop is repeated inside the tool and is unverifiable from the trace |

The change notice is explicit that this is ours to decide: *"Where the parallel boundary falls is
your design judgement, and D2(c) marks the reasoning, not the number… A team that parallelised
less than we did and explained why is on stronger ground than one that copied this page."*

### The honest limits — where parallelising costs us

The brief asks us to find these. Two, both measurable on the shipped set:

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

Same evaluation set, sequential vs parallel.

| | Turns (median) | Input tokens | Cost | Pass rate |
|---|---|---|---|---|
| Sequential | | | | |
| Parallel | | | | |

**Correctness did not move:** [same pass rate, or explain the difference].

### The two honest limits

- Where a parallel call *raised* cost because it turned out to be unnecessary: [...]
- The decision point parallelising removed: [...]
