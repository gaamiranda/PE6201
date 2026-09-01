# D0 · Why an agent at all

**Owner:** [name] · **Feeds:** report §1 (400 words) · **Criterion:** Conceptual Understanding (25%)

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

> **Commit this section before the first agent commit.** Five statements, every one testable —
> if it is not testable, rewrite it. The evaluation set in D4 is downstream of this list.

1. [Names the real cause, traceable to a record — not a plausible story.]
2. [Gives an outcome consistent with what the records actually say.]
3. [Takes the gated action at most once, and only after the facts are established.]
4. [Says "I don't know" rather than inventing an answer the records do not support.] ← the one teams forget; this is what the negative cases exist to catch
5. [Costs less than a person doing it.]
