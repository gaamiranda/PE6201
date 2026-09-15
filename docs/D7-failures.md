# D7 · Two reproduced failures

**Owners:** Goncalo Miranda (failure 1 — loop control) · SUN YUCONG (failure 2 — tool interface or prompt) · JIN CHENG + NIU TONG (scripted reproduction) · **Feeds:** report §5 (250 words) · **Criteria:** Technical Execution + Reasoning

*Deadlines and dependencies: [`../PLAN.md`](../PLAN.md).*

> Each must be built as a **deletion from the working agent** — "the working agent, minus X".
> Putting X back must recover the behaviour. A separately written bad agent does not count: you
> could not then tell whether the fix worked or the rewrite did.

> **Both failures and their before/after tables run on the scripted backend** (change notice,
> 1 Sep). A failure built as a deletion is deterministic *by construction* — that is the point of
> building it that way. Script the observation that causes the loop and it reproduces for ever at no
> cost. **D7 needs no key, and it must reproduce for a marker.**

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

**The deletion:** in `src/tools.py`, revert `check_coverage` from the v2 return shape back to
the old separate branch fields:

```
{"code": code, "covered": bool, "exclusion": str | None,
 "requires_preauth": bool, "document_required": str | None}
```

That is a deletion from the working agent because putting back the shipped v2 shape restores the
behaviour:

```
{"code": code,
 "coverage": {"status": "covered" | "not_covered", "exclusion": str},
 "needed_next": [...]}
```

**Symptom:** the old observation could say one line was excluded while also returning
`requires_preauth` or `document_required` for that same line. The model then had two live branch
signals for a line already refused, so it could chase paperwork for an excluded service and turn a
partial approval into a document request. The scripted backend replays fixed replies, so it cannot
measure the live pass-rate effect here; the deterministic evidence is the interface/guardrail case:
an excluded line now returns `needed_next: []`.

**The fix, and its layer:** tool interface. The fix belongs in the returned object, not in a prompt
sentence, because the unsafe branch should be unrepresentable in the observation the model sees.
The v2 descriptor explains the shape, but the safety property is carried by the data shape.

| | Tokens | Cost | Pass rate | Guardrail cases |
|---|---|---|---|---|
| Broken | 833,198 input + 73,434 output estimated tokens in the committed scripted baseline | US$0.112697 projected for the 76-trial schedule | 52/76 code, 38/42 decision-only cases; pass-rate comparison not attributable on scripted replay | 9/10: the excluded-line/no-paperwork case fails because the old shape can expose branch flags on a refused line |
| Fixed | 999,600 input + 73,434 output estimated tokens after the v2 descriptor/shape | US$0.129332 projected for the 76-trial schedule | Expected unchanged on scripted replay; live comparison belongs to the later battery | 10/10: excluded lines have `needed_next: []`, so the unsafe branch is not present |

---

## For both failures

**Which layer the fix belongs in, and why the other two were the wrong place.**
*That judgement is most of the mark.*

| Failure | Right layer | Why not code | Why not tool interface | Why not prompt |
|---|---|---|---|---|
| 1 | Loop control | The fix is code: the loop must remember repeated actions and cap spend. | A tool cannot know whether the same action has already happened in this run. | A prompt reminder still lets a model repeat itself; it does not bound cost. |
| 2 | Tool interface | Ordinary validation can reject bad records after the model has already taken the wrong branch. | This is the right layer: make the unsafe observation shape impossible. | A prompt sentence such as "ignore paperwork for excluded lines" is paid every turn and can still be missed. |
