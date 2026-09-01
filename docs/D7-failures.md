# D7 · Two reproduced failures

**Owner:** [name] · **Feeds:** report §5 (250 words) · **Criteria:** Technical Execution + Reasoning

> Each must be built as a **deletion from the working agent** — "the working agent, minus X".
> Putting X back must recover the behaviour. A separately written bad agent does not count: you
> could not then tell whether the fix worked or the rewrite did.

---

## Failure 1 · Loop control — required

**The deletion:** [which guard was removed, and where]

### 1 · The instrumentation that found it

Per run we log: turns used, tokens in/out, estimated cost, whether a cap fired, and the tools called
in order. Without this a runaway loop is invisible — it raises no exception, it just costs more.

### 2 · The turn distribution across the whole evaluation set

> One number is not a distribution.

| | Median | Worst case | Runs that hit the step cap |
|---|---|---|---|
| | | | |

### 3 · The fix, in the code layer

**What actually caught it:** [action de-duplication / step cap / budget ceiling]

**Why the other two would not have:** [...]

### 4 · Before and after

| | Turns | Tokens | Cost | Pass rate |
|---|---|---|---|---|
| Broken | | | | |
| Fixed | | | | |

**The pass rate did not fall:** [a step cap that stops a runaway also truncates a legitimate long
run — show this.]

---

## Failure 2 · A different layer

Must sit in the **tool interface** or the **prompt** — not loop control again.

**The deletion:** [...]
**Symptom:** [...]
**The fix, and its layer:** [...]

| | Tokens | Cost | Pass rate | Guardrail cases |
|---|---|---|---|---|
| Broken | | | | |
| Fixed | | | | |

---

## For both failures

**Which layer the fix belongs in, and why the other two were the wrong place.**
*That judgement is most of the mark.*

| Failure | Right layer | Why not code | Why not tool interface | Why not prompt |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
