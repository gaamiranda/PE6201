# D0 · Why an agent at all

**Owner:** ZHENG YONGJIE · **Feeds:** report §1 (400 words) · **Criterion:** Conceptual Understanding (25%)

*Deadlines and dependencies: [`../PLAN.md`](../PLAN.md).*

> Answered **before any code**. This is the first thing the marker reads, and the commit history is
> checked.

**This file and report §1 are two artefacts, not one.** This file is the long version: tables, case
ids, evidence, no length limit. Report §1 is a **400-word** distillation written last, once `P` and
`T` exist. Every value marked `[pending]` is a tracked dependency on the 10 Sep freeze checklist
([`../PLAN.md`](../PLAN.md) §5), not an omission.

**Where the numbers in this file come from.** Every figure below is either produced by a command
stated beside it, or marked `[pending]`. Nothing here is estimated and presented as measured —
brief §6, condition 2. The two commands are:

```bash
cd src && python3 bench_ground_truth.py     # the D0(b) test 1 latency table
cd src && python3 -c "import loop; r=loop.run_case('CLM-8842'); print(r['usage'])"
```

---

## D0(a) · Place the problem on the ladder, and defend the rung

A2 sits on **rung 7**, and the brief chose that for us. So the job is not to justify rung 7 — it is
to say what rungs 1–6 would and would not have delivered on our problem, and what rung 7 cost us.

Problem A is on rung 7 because the model selects its next action from evidence returned during the
run: which lines to price, whether a pre-authorisation is needed at all, and whether to stop early.

| Rung | Would it have worked here? | What it would have missed |
|---|---|---|
| 1 · Single call | Only by pre-loading every record for every claim into one prompt | Selective retrieval and early exit. `CLM-8910` is decidable from two records; a single call pays for all of them on every claim |
| 2 · Prompt chain | Yes, for a fixed claim shape | Fixed steps run checks the claim does not need. A one-line claim with no pre-authorisation requirement would still walk the pre-authorisation step |
| 3 · Routing | Picks a lane once, at the start | The lane is not knowable at the start. Whether `CLM-8888` is an approve or a request-document is only settled *after* `check_coverage` returns `requires_preauth` |
| 4 · Parallelisation | Collapses the independent checks — and we do use this, inside the loop (D2(c)) | It cannot remove a **dependency**. Pre-authorisation is checked only for the lines coverage said needed one, so it cannot be fanned out alongside coverage |
| 5 · Orchestrator–workers | Splits the work at runtime | No re-query on what a worker found, and **no write**. It plans, fans out and merges; it does not loop on evidence and it does not act |
| 6 · Evaluator–optimiser | Improves an answer it already has | It never decides *what evidence to retrieve next*, and it also does not write |
| 7 · Agent | **chosen** | cost: turns unbounded until we cap them, spend unpredictable per claim, and paths no longer enumerable — we test outcomes, not paths |

**We concede the honest point:** a deterministic workflow could implement Problem A as it stands,
because the current routing rules can be written as a decision tree. Rung 7 is justified not as the
only possible build, but because the number of steps varies with the claim — a decision tree matches
that only by enumerating every path in advance, and every new exclusion or document rule adds paths.

### 1 · The workflow test

The four questions, answered against our own set. **The second row is the one that decides it.**

| The question | Our answer |
|---|---|
| Who decides the sequence of steps, and when? | The model, at runtime. We fix the tools, the routing rule and the caps; we do not fix the order |
| **Does the number of steps vary with the input?** | **Yes — 2 turns to 5 turns, measured end to end on the scripted backend (below), before we add the longer cases** |
| Can you test every path? | **No.** We test *outcomes*, not paths — which is why D4 is an outcome-labelled answer key (`expected_decision` + `must_record`) and not a set of path assertions |
| What does it cost? | Unpredictable per claim until capped, and we have already been bitten: one live run made **60 model calls and burned 307,823 input tokens** on a claim that needed four tool calls. `Guards.step_cap`, `call_cap` and `budget_ceiling_usd` exist because of it — values `[pending: D5(a)]`, [`../src/loop.py`](../src/loop.py) |

Shown with cases from our own evaluation set, under **our** dependency rule — two calls may share a
turn only when neither consumes the other's output.

**Shortest legitimate run — `CLM-8910`, measured at 2 turns, 4 tool calls, 3 model calls.**

```
turn 1   get_claim("CLM-8910")
turn 2   lookup_policy(M-4471, 2026-09-11) ‖ get_hospital_status(H-114) ‖ check_claim_history(...)
         -> POL-5588 lapsed 2026-03-31.  ESCALATE, trigger policy_lapsed.
```

The claim cannot be decided at this level regardless of coverage, so pricing the individual lines
would burn turns on a decision the run was never going to make. **The early exit is correct
behaviour, not a truncated run** — and the answer key rewards it. `CLM-8925` (SGD 11,400 of lines
against SGD 9,200 of remaining annual limit on POL-3310) and `CLM-8933` (a duplicate of the
already-decided `CLM-8710`, matched on all four facts) exit on the same shape and for the same
reason: the deciding fact arrives in turn 2 and nothing after it can change the outcome.

**Longest ordinary run — `CLM-8842`, measured at 5 turns, 9 tool calls, 6 model calls.**

```
turn 1   get_claim("CLM-8842")                                    -> 3 lines
turn 2   lookup_policy(M-2214, 2026-09-02) ‖ get_hospital_status(H-114) ‖ check_claim_history(...)
turn 3   check_coverage(POL-3310, 47120) ‖ (…, 62480) ‖ (…, 31255)
turn 4   get_preauthorisation(M-2214, 62480, 2026-09-02)          <- only this line needed one
turn 5   issue_decision_letter(...)                               <- gated, and a turn like any other
```

Three lines, one excluded under `EX-14`, one needing `PA-5521` chased. Nine calls in five turns;
run one call per turn and the same nine calls take **nine turns**.

> **What "measured" means here, precisely.** These counts come from
> `loop.run_case()` on the scripted backend, which replays hand-written transcripts
> ([`../src/dev_transcripts.py`](../src/dev_transcripts.py)). They therefore measure **our
> dependency rule executing correctly**, not a model's judgement — the transcripts take the
> shortest legal path, so they are a **lower bound on `T`**, and a live model will sit at or above
> them. The distribution that matters for the arithmetic in D0(b) is the live one:
> `[pending: D5(a)]`. Stating this distinction is the point; a turn count quoted without saying
> which backend produced it is not a measurement.

**Why five and not the brief's four.** Appendix A shows `CLM-8842` in four turns, folding
`check_coverage` into turn 2 beside `lookup_policy`. That grouping is only reachable if
`check_coverage` performs the member → policy hop itself. We made it take a **`policy_id`** instead,
because that makes a coverage check against a policy the member does not hold *unrepresentable* —
and it costs exactly one turn. **A poka-yoke bought for a turn, deliberately**, and it is the
clearest single example of what rung 7 costs us: the safety property is cheap, the turn is not,
and only measurement settles whether the trade was right. D2(c) carries both groupings.

### 2 · The two conditions

- **Steps not known in advance.** The sequence depends on earlier observations. `check_coverage`
  decides whether `get_preauthorisation` is called at all; `lookup_policy` can end the run before any
  line is priced. Take this away and we have a workflow.
- **Ground truth back at every step.** Every tool call returns a record from a system of record — a
  policy row, a coverage decision, a pre-authorisation window — so reality can correct the model
  inside the run. Take this away and it is a monologue: fluent, self-consistent and unfalsifiable.
  Detail in D0(b) test 1.

### 3 · The three-question test — where the governance cliff is

The cliff is not retrieval → agentic retrieval. It is **agentic retrieval → agent, at the first write.**

**Our first irreversible action:** `issue_decision_letter(record)` — one log record, not a composed
letter (D1 scope boundary).

**Why that write puts us on rung 7 rather than 5 or 6.** Everything before it is agentic retrieval:
the model picks what to retrieve, it re-queries on what it finds, and it changes nothing. A rung-5
orchestrator and a rung-6 evaluator also decide things at runtime — what neither does is **act on
the world**. Once a member has been told "approved in principle", walking it back is expensive, and
that single state-changing call is what moves the system from a read-only loop we can let iterate
unattended to one that needs an autonomy gate, a step cap and a budget ceiling. The gate covers
exactly one tool because there is exactly one write.

**Read the ladder claim precisely.** Six of our seven tools are read-only, so on the three-question
test the *retrieval half* of our system is agentic retrieval, not an agent. It is the seventh tool
that carries the rung. That is why D3's gate sits in front of `issue_decision_letter` and not in
front of the loop: gating the reads would buy nothing and cost every turn.

### 4 · Where a ReAct loop stops being the right architecture

Naming the rung above is only half the argument; the marker also asks where our own rung stops
working. Three boundaries, each with the evidence that would tell us we had crossed it, so this is
a falsifiable claim rather than a preference:

| Boundary | What would tell us we had crossed it | What we would build instead |
|---|---|---|
| **The trajectory gets long.** `s = P^(1/T)` compounds: at a fixed `s`, doubling `T` is not a small tax | Median `T` climbing past roughly 10–12 while `P` falls, with no single weak step to blame | Cut `T` first (D2(c), move work into ordinary code). If `T` will not come down, the routing rules have outgrown a single loop and belong in a workflow with the model called at the branch points only |
| **The write stops being single and reversible-in-principle.** One gated call is governable by one gate | A second irreversible action, or one that touches money rather than a log line | Not more autonomy but less: `suggest`, with the act moved out of the loop entirely. The FAQ's own reference implementation gates one call, not a set |
| **The judgement step has no fast, objective signal.** Our narrative-reading step already has none | The weakest-step analysis (test 2) landing on the narrative turn and staying there after a descriptor rewrite | A classifier or a rule in code in front of the loop, so the unfalsifiable step stops being a *turn* the agent can wander on. This is D0(b) test 1's honest half, turned into a design consequence |

**And the architecture we did not build.** A second agent reviewing the decision record before the
write would plausibly catch statement 1 and statement 4 failures — a fabricated exclusion, an
approval around a missing document. We did not build it, for three reasons that are evidence rather
than taste: it is out of scope (brief §3, D1); it roughly doubles per-run token cost for a pass-rate
gain we have not yet shown we need, and D6 layer 2 is what decides whether that trade pays; and
Cognition's own reversal (Pre-read 5) reports keeping **writes single-threaded** even in the
multi-agent version they now ship. The cheaper version of the same idea is already in the loop and
costs nothing per call: `unsupported()` in [`../src/loop.py`](../src/loop.py) refuses a record the
evidence trail does not support. Report §6 carries the full paragraph.

---

## D0(b) · When NOT to build an agent — both tests, answered honestly

### Test 1 · The ground-truth test

What will tell this loop it is wrong, and how fast?

**Measured** — `cd src && python3 bench_ground_truth.py`, median of 2,000 calls each, arm64 macOS,
Python 3.9.6, 6 Sep 2026. Re-run it and paste the output; do not retype these by hand.

| System of record | What it can contradict | Median read |
|---|---|---|
| `claims.json` | Nothing on its own — it is the question, not the answer. Listed because the narrative arrives here, and it is the only field an outsider wrote | 0.75 µs |
| `policies.json` | An assumed-active policy (`POL-5588` lapsed, `CLM-8910`); a date of service outside the policy's own window (`POL-6001` starts 12 days after treatment, `CLM-8917`); a total over the remaining annual limit (`CLM-8925`) | 0.79 µs |
| coverage (`procedures` + `policies.exclusions` + `required_documents`) | Whether a line is payable at all, whether it needed a pre-authorisation, and which document it requires | 0.58 µs |
| `preauthorisations.json` | An approval that exists but expired before the date of service — `PA-5640` ended 2026-05-31 (`CLM-8894`) | 0.88 µs |
| `hospitals.json` | Panel status — which changes what the record must *say*, not what the decision is (`H-330`, `CLM-8874`) | 0.25 µs |
| `decided_claims.json` | That this claim was already decided under another id (`CLM-8710` → `CLM-8933`) | 4.38 µs |

Loading all eight fixture files once, at import: **0.207 ms**, paid per process rather than per call.

**Fast and objective, so we build the agent and wire that signal in first.** Every read above is
single-digit microseconds against a model call of one to three seconds. Ground truth is roughly
**six orders of magnitude cheaper than the reasoning it corrects**, which is what allows the
retrieval loop to iterate without a human in each turn. In our build these are local JSON; in
production they are a policy database and a claims system, and the property that matters —
objective, and back inside the run — is the same one. The absolute number would move by orders of
magnitude on a real database and the argument would not, because the comparison is against seconds.

**One row is not like the others, and it will drift.** `check_claim_history` is the only tool that
is not a keyed lookup: it scans `decided_claims.json` linearly, which is why it is 5–17× the others
at 4 rows and will grow as the case baton takes that table towards ~60 (`PLAN.md` §3). Re-run the
benchmark after the freeze. It is still four orders of magnitude below a model call, so nothing in
the argument turns on it — but a table that silently goes stale is exactly the failure the brief's
"figures are measurements you ran" condition is aimed at.

**The honest half.** Not every step has ground truth like this.

- **The write does not get one.** Fast feedback licenses the *loop*, not the *action*.
  `issue_decision_letter` stays behind the autonomy gate regardless of how fast the reads are.
- **Selecting the right evidence is still on the agent.** A record only contradicts a claim if the
  model went and read it. `CLM-8917` is the case: the policy is live, so a run that checks `status`
  and stops never asks the question the date window would have answered. Our answer is a poka-yoke
  rather than an instruction — `lookup_policy` *requires* `date_of_service` and computes
  `covers_date_of_service` itself, so the check cannot be skipped by forgetting it.
- **One step has no fast, objective signal at all — reading the member's free-text narrative.**
  Nothing in the fixtures contradicts a misreading of it within the turn. That is why `CLM-8941` and
  `CLM-8952` exist, why the guardrail layer (D3) treats narrative text as data and never as
  instruction, and why we expect this to be the weak step when we go looking for one in test 2.

### Test 2 · The arithmetic

> The exponent is **steps in ONE run**, not cases in the evaluation set.

```
measured run pass rate       P = [pending: D4 labels + the D5(a) run]
measured median turns        T = [pending: D5(a), live]
implied per-step reliability s = P^(1/T) = [pending]
```

**No final value is estimated here.** This closes when D4 and D5(a) land; it is item 1 on the
10 Sep freeze checklist, owned by ZHENG YONGJIE. Report §1 requires the figure, not the formula.

**What is already fixed is the machinery and the sensitivity, and neither depends on the final
numbers.** The worked substitution below uses the brief's own illustrative `P = 0.78` against **our
measured turn range**, so that on 10 Sep only two numbers change and no reasoning does:

```
illustrative        P = 0.78   over our measured shortest run   T = 2
                    s = 0.78^(1/2) = 0.883
then hold s and vary T, which is the only lever D2(c) moves:
    T = 2   (CLM-8910, measured)   ->   0.883^2  = 0.78
    T = 5   (CLM-8842, measured)   ->   0.883^5  = 0.54
    T = 9   (CLM-8842, one call per turn — D2(c)'s "before")   ->   0.883^9  = 0.33
```

Read the last two lines together, because that pair **is** D2(c)'s business case: the same nine tool
calls, the same model, the same per-step quality — and predicted run success of 0.54 folded versus
0.33 sequential. Whatever `s` turns out to be, that gap is the return on the dependency rule, and it
is why cutting `T` is Class 4's biggest of the three ways out. The measured before-and-after over
the whole set is `[pending: D5(a)]`.

> Two cautions on our own illustration, stated because a marker will apply them anyway. First, the
> scripted `T` values are a lower bound (see D0(a)) — a live median will be higher, which makes
> `s^T` worse, not better. Second, `s` derived at `T = 2` and then applied at `T = 9` assumes steps
> are independent and equally reliable, and neither is true. It is a diagnostic, not a prediction.

These are not three separate exercises:

```
D2(c) folds independent calls into one turn   ->  T falls
T falls, s unchanged                          ->  P = s^T rises
P rises                                       ->  D6 layer 2 = (1 - P) x 7.60 falls
```

One argument, measured three times. A claims assessor costs **US$7.60** per escalated claim
(US$38/h × 12 min), so every point of `P` is worth 7.6 cents per claim before a single token is
counted.

**Which is our problem — step quality or step count?** `[pending — and this is the sentence the
report needs]`

**Weakest step**, found by grouping failing runs by the tool call immediately before things went
wrong: `[pending: the D5(a) trace log]`. The loop already records `tools_called` in order on every
run, so the grouping is a query over results we will have, not new instrumentation. Our prior is the
narrative-reading step, for the reason in test 1. Fixing it raises `s`; removing it lowers `T`;
**an unreliable step usually costs both** — when a turn returns something poor the agent re-reads,
retries or wanders, so `s` falls and `T` inflates at the same time. That is why D7's loop failure and
this arithmetic are one investigation seen from two ends, and we have already seen the mechanism
once: the 60-call run in D0(a) is `T` inflating with no bad *outcome* to show for it.

**The limits, stated because they are real.** Steps are not independent — a bad observation early
makes later steps worse, not equally likely to succeed — and they are not equally failure-prone: the
turn that reads a policy row is near-perfect (0.79 µs and no judgement in it), the turn that judges a
free-text narrative is not. `s` is a diagnostic for *"is my problem step quality or step count?"*,
not a physical constant of our system.

---

## D0(c) · What good looks like

> **Committed before the first agent commit** — the commit history is checked. Five statements, every
> one testable. The evaluation set in D4 is downstream of this list, so a statement here that no case
> can check is a statement that does not exist.

Written against Problem A specifically, not copied from Class 4's shipping example. The five
statements are unchanged since they were committed; what has been added below each is the *test
hook* — the case id or code check that makes it checkable, which is what the brief asks a statement
to have.

**Each hook says which kind of check it is**, because the brief marks that distinction: an
**evaluation case** asks *did it get the job right*; a **guardrail case** asks *did it refuse, cap or
escalate when it should have*. They live in different files — the answer key
([`../A2_reference_data/expected_outcomes_A.json`](../A2_reference_data/expected_outcomes_A.json))
and the ten-case checklist
([`../evaluation/guardrail-checklist.md`](../evaluation/guardrail-checklist.md)) — and a statement
tested by the wrong one is a statement that is not really tested.

A good run:

**1 · Names the real cause, traceable to a record — not a plausible story.**
Every line item carries a disposition that points at something in the data: a coverage decision, a
named exclusion rule, or a pre-authorisation reference with its validity window. Never at a plausible
reading of the member's narrative.
*Tested by (evaluation set):* `must_record` on every ordinary case in the answer key — `CLM-8842`
requires `31255` refused under `EX-14` and `PA-5521` cited for `62480`, by name. `CLM-8850` and
`CLM-8960` require naming the prior claim that *almost* matched (`CLM-8702`, `CLM-8726`) and the one
fact that differed, which no plausible story can supply.
*Also enforced in code:* `unsupported()` refuses a record whose trigger no tool call establishes.

**2 · Gives the outcome the routing table requires, for the facts it actually found.**
A partly payable claim is an **act**: three lines approved and one excluded is one decision letter
covering both, not an escalation. Escalate when the claim cannot be *decided* — not when a line is
refused.
*Tested by (evaluation set):* `CLM-8842` (partly payable → `approve_in_principle`) against `CLM-8925`
(over the limit → `escalate`); and `CLM-8941`, where an excluded line and an injected instruction sit
in the same claim and only the injection is the trigger. The trigger is code-checked as well as the
decision — the right outcome by the wrong trigger is not a pass (`TrialResult.trigger_ok`).

**3 · Takes the gated action at most once, and only after the facts are established.**
`issue_decision_letter` fires once per claim or not at all, after the policy, every line and the
hospital have resolved, and only once the autonomy gate is satisfied. An escalation reaches it zero
times and records that it deliberately did not act.
*Tested by (guardrail checklist):* cases 6 and 7 — the same gated action attempted twice, and the
gated action attempted before operator confirmation.
*Also code-checked on every evaluation run:* a count of gate calls in `usage["tools_called"]`.

**4 · Says "I don't know" rather than inventing an answer the records do not support.**
When a required fact is absent — no pre-authorisation, no itemised bill — the run names the exact
missing item and the line it belongs to, then stops. It never supplies the fact, infers it, or
approves around it. "More information" is not an answer.
*Tested by (evaluation set, negative cases, 3 trials each):* `CLM-8888` (names line `62480` and the
date it must be valid on), `CLM-8894` (finds `PA-5640`, states its window ended 2026-05-31, and says
that is *why*), `CLM-8901`, and every negative case we add.
**This is the one teams forget, and it is what the negative cases exist to catch.**

**5 · Costs less than a person doing the same first response — which means it stops as soon as the
outcome is established.**
A claims assessor costs US$7.60 per escalated claim (US$38/h × 12 min). A good run costs less than
that all-in: its own tokens **plus** the expected cost of the runs it gets wrong, `(1 − P) × 7.60`. A
cheap agent that is wrong half the time is not cheap. Turns are the other half of the bill — once a
decisive escalation condition is established, further checks are spend on a decision the run will
never make.
*Tested by:* D6 layer 1 + layer 2 at the measured pass rate; and a turn-count check on `CLM-8910`,
`CLM-8925` and `CLM-8933`, all three of which must finish short of the ordinary path — measured at
2 turns against `CLM-8842`'s 5.

> Statements 1 and 4 are the ones an eloquent model fails. Statement 3 is the governance one.
> Statement 5 is the only one that can be true while the other four are false — which is why it is
> last, not first.
