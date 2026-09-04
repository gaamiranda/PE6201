# D0 · Why an agent at all

**Owner:** ZHENG YONGJIE · **Feeds:** report §1 (400 words) · **Criterion:** Conceptual Understanding (25%)

*Deadlines and dependencies: [`../PLAN.md`](../PLAN.md).*

> Answered **before any code**. This is the first thing the marker reads, and the commit history is
> checked. A team that skips it and goes straight to building loses marks in two criteria.

---

## D0(a) · Place the problem on the ladder, and defend the rung

A2 sits on **rung 7**, and the brief chose that for us. So the job is *not* to justify rung 7 — it is
to say what rungs 1–6 would and would not have delivered on our problem, and what rung 7 cost us.

| Rung | Would it have worked here? | What it would have missed |
|---|---|---|
| 1 · Single call | | |
| 2 · Prompt chain | | |
| 3 · Routing | | |
| 4 · Parallelisation | | |
| 5 · Orchestrator–workers | | |
| 6 · Evaluator–optimiser | | |
| 7 · Agent | chosen | cost: [unbounded turns until capped, unpredictable spend, no enumerable test paths] |

### 1 · The workflow test

The deciding row is **does the number of steps vary with the input?** Show it with cases from our own
evaluation set — name them.

- Shortest legitimate run: case `[id]`, [n] turns, because [...]
- Longest legitimate run: case `[id]`, [n] turns, because [...]

### 2 · The two conditions

- **Steps not known in advance:** [...]
- **Ground truth back at every step:** [...] — without this it is a monologue: fluent, self-consistent, unfalsifiable.

### 3 · The three-question test — where the governance cliff is

The cliff is not retrieval → agentic retrieval. It is **agentic retrieval → agent, at the first write.**

- **Our first irreversible action:** `[issue_decision_letter / book_slot]`
- Why that write puts us on rung 7 rather than 5 or 6: [...]

---

## D0(b) · When NOT to build an agent — both tests, answered honestly

### Test 1 · The ground-truth test

What will tell this loop it is wrong, and how fast?

| System of record | What it can contradict | How fast it answers |
|---|---|---|
| | | |

Fast and objective → build the agent, wiring that signal in first. Slow or subjective → a workflow
with a human gate.

### Test 2 · The arithmetic

> The exponent is **steps in ONE run**, not cases in the evaluation set.

Fill in once D4 and D7 have numbers:

```
measured run pass rate      P = [ ]
measured median turns       T = [ ]
implied per-step reliability s = P^(1/T) = [ ]

at T = [shorter]  ->  s^T = [ ]
at T = [longer]   ->  s^T = [ ]
```

**Which is our problem — step quality or step count?** [one sentence, and this is the sentence the
report needs]

Weakest step, found by grouping failing runs by the tool call immediately before things went wrong:
`[tool]`. Fixing it raises `s`; removing it lowers `T`; an unreliable step usually costs us both.

---

## D0(c) · What good looks like

> **Committed before the first agent commit** — the commit history is checked. Five statements,
> every one testable: if it is not testable, rewrite it. The evaluation set in D4 is downstream of
> this list, so a statement here that no case can check is a statement that does not exist.

**Draft — owner ZHENG YONGJIE to review and put in his own words before the report.** These are
written against Problem A specifically, not copied from Class 4's shipping example.

A good run:

**1 · Names the real cause, traceable to a record.**
Every line item carries a disposition that points at something in the data — a coverage decision, a
named exclusion rule, or a pre-authorisation reference with its validity window. Never at a
plausible reading of the member's narrative.
*Tested by:* `must_record` on every ordinary case in the answer key.

**2 · Gives the outcome the routing table requires, for the facts it actually found.**
In particular, a partly payable claim is an **act**: three lines approved and one excluded is one
decision letter covering both, not an escalation. Escalate when the claim cannot be *decided* — not
when a line is refused.
*Tested by:* `CLM-8842` (partly payable → approve) against `CLM-8925` (over the limit → escalate).

**3 · Takes the gated action at most once, and only after the facts are established.**
`issue_decision_letter` fires once per claim or not at all, after the policy, every line and the
hospital have resolved, and only once the autonomy gate is satisfied. An escalation reaches it zero
times and records that it deliberately did not act.
*Tested by:* a code check that counts gate calls; guardrail cases 6 and 7.

**4 · Says "I don't know" rather than inventing an answer the records do not support.**
When a required fact is absent — no pre-authorisation, no itemised bill — the run names the exact
missing item and the line it belongs to, then stops. It never supplies the fact, infers it, or
approves around it. "More information" is not an answer.
*Tested by:* `CLM-8888`, `CLM-8894`, `CLM-8901`, and every negative case we add.
**This is the one teams forget, and it is what the negative cases exist to catch.**

**5 · Costs less than a person doing the same first response.**
A claims assessor costs US$7.60 per escalated claim (US$38/h × 12 min). A good run costs less than
that all-in — its own tokens **plus** the expected cost of the runs it gets wrong,
`(1 − P) × 7.60`. A cheap agent that is wrong half the time is not cheap.
*Tested by:* D6 layer 1 + layer 2, at the measured pass rate.

> Statements 1 and 4 are the ones an eloquent model fails. Statement 3 is the governance one.
> Statement 5 is the only one that can be true while the other four are false — which is why it is
> last, not first.
