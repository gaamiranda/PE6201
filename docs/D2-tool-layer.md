# D2 · The tool layer

**Owner:** [names] · **Feeds:** report §2 (450 words) · **Criteria:** Technical Execution + Reasoning

> The tool descriptions and signatures are the entire manual the model gets. It cannot ask a
> colleague, hover a tooltip, read our source, or try it in staging.

---

## D2(a) · The tool set — chosen, not collected

Every tool we ship, scored against the three questions.

| Tool | 1 · Does a task fail without it? | 2 · Confusable with a neighbour? | 3 · Cost when never called | Verdict |
|---|---|---|---|---|
| | | | | keep / cut |

**Before adding a tool we tried not adding one.** Record which move we used, in order of preference:

1. Widened an existing tool's parameters — [where, or "not used"]
2. Returned more from one call — [where, or "not used"]
3. Moved the step out of the loop into ordinary code — [where, or "not used"]
4. Added the tool — [which, and the *observed* failure that justified it]

**Tools we removed** (this earns explicit credit — the brief calls it "the behaviour nobody does naturally"):

| Tool removed | The observation that removed it | Effect on pass rate | Effect on tool-block tokens |
|---|---|---|---|
| | | | |

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
| | | |
| | | |

### The measured rewrite

One tool, v1 vs v2 of its descriptor and return shape.

| | Tokens returned per call | Eval pass rate | Guardrail cases passed |
|---|---|---|---|
| v1 | | | |
| v2 | | | |

**Verdict:** [what changed, and why]. If v2 is not smaller or not safer, say so — a rewrite that did
not help, honestly reported, scores better than one that was never measured.

---

## D2(c) · Calling more than one tool in a turn

### The dependency rule

A pair may go in parallel **only when neither needs the other's output.**

| May run together | Must run alone / after | Why |
|---|---|---|
| | | |

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
