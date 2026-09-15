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

**The deletion:** `Guards(dedup=False)` in `src/loop.py` — remove action de-duplication, the
loop's memory of what it has already done. Nothing else changes. Putting the flag back recovers
the behaviour exactly, which is what makes this a deletion from the working agent rather than a
separately written bad agent.

Reproduce with `python3 evaluation/reproduce_failure_1.py` — scripted backend, no API key,
US$0.00, deterministic. Output is written to `evaluation/failure_1_run.json`.

**The symptom:** the agent re-issues an identical `issue_decision_letter(record)` and the claim is
appended to `results/decisions.jsonl` once per attempt. One claim, four payment records. In a real
insurer that is the claim paid four times.

### 1 · The instrumentation that found it

Per run the loop logs turns, model calls, tokens in and out, estimated cost, which cap fired, and
**every tool called, in order**. That last field is the only one that shows this failure. The
repeat appears as `issue_decision_letter` four times in `tools_called` and as four lines in the
decision log; it appears in no summary statistic we report.

This one was found live, not by reasoning. The same instrumentation caught the related runaway
recorded in `loop.py`: `CLM-8850` on a live gpt-4o-mini made 60 model calls and burned 307,823
input tokens while `turns` sat at 4, because the model kept emitting replies carrying neither an
Action nor a Final. That is why `call_cap` counts model calls rather than turns.

### 2 · The turn distribution across the whole evaluation set

> One number is not a distribution.

Measured with the caps lifted to 20/30, so that nothing is truncated by the number being
measured, then re-checked under the shipped guards:

| | Median | p90 | Worst case | Runs that hit a cap under shipped guards |
|---|---|---|---|---|
| Turns per run, all 42 cases | 5 | 8 | 9 | 0 (`step_cap` 12) |
| Model calls per run, all 42 cases | 7 | 9 | 12 | 0 (`call_cap` 22) |
| Unproductive rounds per run | 0 | 2 | 6 | not capped — only `call_cap` bounds it |

And the measurement that actually matters here:

| | Tool calls executed across all 42 cases |
|---|---|
| Shipped (`dedup=True`) | 212 |
| Minus dedup (`dedup=False`) | 212 |

**De-duplication suppressed zero calls across the entire evaluation set.** A suppressed call never
reaches `tools_called`, so equal totals — 212 in both arms — mean the guard never fired once. Turns,
tokens, cost and the 40/42 decision rate are identical.

That is the uncomfortable part of this deliverable and we are reporting it rather than hiding it:
**on our own evaluation set this guard is indistinguishable from dead code.** A team measuring only
pass rate would have deleted it as unused. It is insurance against a behaviour our recorded model
does not exhibit — and the moment a model does exhibit it, the cost is paid in duplicate approvals,
not in a failed test.

Worth recording that this figure moved with the prompt. An intermediate recording, made while the
tool manual was still teaching the model a syntax the parser rejected, gave **three** suppressions:
the model was repeating itself because it was stuck, not because it was looping over work. Fixing
the prompt removed the repeats and returned this guard to zero. A guard's hit rate measures the
prompt as much as the guard.

### 3 · The fix, in the code layer

**What actually caught it:** action de-duplication. The loop fingerprints tool name, positional
args and keyword args; a repeat returns the earlier observation instead of executing the action
again. The repeat is *answered* rather than ignored, because silence invites the model to try
again.

**Why the other two would not have.** Both were measured, not assumed — the third row is the
induced repeat left to run unbounded:

| Guard | Does it stop the duplicate write? | Measured |
|---|---|---|
| Action de-duplication | **Yes — prevents it.** The second attempt never executes | 4 write actions → **1** letter |
| Step cap | No — it *bounds* it. The run is stopped, but only after the damage | unbounded repeat → **8** letters before `step_cap` fired at turn 12 |
| Budget ceiling | No. Duplicate writes are cheap; this run cost US$0.00230 and never approached US$0.016 | never fired |

The step cap is the instructive one. It does end the run, so a team that measured only "did the
loop stop?" would call it sufficient. It stopped this one after **eight** duplicate payment
records. A guard that limits how many times you pay a claim twice is not a guard against paying a
claim twice.

### 4 · Before and after

Whole evaluation set, both arms:

| | Turns (median/max) | Tool calls | Tokens in | Cost | Pass rate |
|---|---|---|---|---|---|
| Broken (`dedup=False`) | 5 / 9 | 212 | 473,596 | US$0.08786 | 40/42 |
| Fixed (`dedup=True`) | 5 / 9 | 212 | 473,596 | US$0.08786 | 40/42 |

The induced repeat, which is where the two arms separate at all:

| | Letters written | Write actions attempted | Turns | Tokens in | Cost |
|---|---|---|---|---|---|
| Broken (`dedup=False`) | **4** | 4 | 8 | 13,660 | US$0.00230 |
| Fixed (`dedup=True`) | **1** | 4 | 8 | 13,768 | US$0.00231 |

**The pass rate did not fall — and that is the finding, not a footnote.** Every aggregate number
in the first table is identical across the two arms: same turns, same tool calls, same tokens,
same cost, same 40/42. A guard that stops a runaway normally also truncates a legitimate long run,
so the usual thing to show here is that the pass rate survived the guard. This guard does not cost
even that. The fixed arm is US$0.00002 *more* expensive on the induced case, because answering the
repeat with the earlier observation is slightly more text than executing it again.

So the honest statement of this failure is not "the pass rate held up". It is: **our reported
metrics cannot see this failure at all.** Four duplicate approvals and one correct approval score
identically on every number in the results table. The only evidence is the ordered `tools_called`
field and the line count of the decision log, and the only reason we tested for it is that the
gated action is the one thing in this system that changes the world. That is the argument for
instrumenting actions rather than outcomes, and it is why `evaluation/guardrail-checklist.md`
row 6 exists as a standing test.

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
| Broken | 833,198 input + 73,434 output estimated tokens in the committed scripted baseline | US$0.112697 projected for the 76-trial schedule | 52/76 code, 38/42 decision-only cases; pass-rate comparison not attributable on scripted replay | 9/10, and **not the same 9**: row 2 (`CLM-8952`) fails under both shapes, and the old shape additionally lets an excluded line carry `requires_preauth`/`document_required` — a contradiction the checklist has no row for, because after the rewrite it is unrepresentable |
| Fixed | 999,474 input + 73,434 output estimated tokens after the v2 descriptor/shape | US$0.129324 projected for the 76-trial schedule | Unchanged on scripted replay, and *necessarily* so — see the note below; the live comparison belongs to the battery | 9/10: excluded lines return `needed_next: []`, so the contradictory observation is gone. Row 2 still fails, for an unrelated reason the shape change was never going to fix |

---

## For both failures

**Which layer the fix belongs in, and why the other two were the wrong place.**
*That judgement is most of the mark.*

| Failure | Right layer | Why not code | Why not tool interface | Why not prompt |
|---|---|---|---|---|
| 1 | Loop control | The fix is code: the loop must remember repeated actions and cap spend. | A tool cannot know whether the same action has already happened in this run. | A prompt reminder still lets a model repeat itself; it does not bound cost. |
| 2 | Tool interface | Ordinary validation can reject bad records after the model has already taken the wrong branch. | This is the right layer: make the unsafe observation shape impossible. | A prompt sentence such as "ignore paperwork for excluded lines" is paid every turn and can still be missed. |

---

## A note on what the scripted backend can and cannot show for failure 2

`evaluation/transcripts.jsonl` is keyed on `(case_id, turn)` alone. It does not record which prompt
or which tool-return shape produced each reply, so on replay the model's replies are fixed no matter
what the tool layer does underneath them.

That was verified rather than assumed: making `check_coverage` return a deliberately wrong object
for every line — `{"code": "SABOTAGE", "coverage": {"status": "covered"}, "needed_next": []}` —
leaves the harness output **byte-identical** at 63/76 code, 40/42 decision-only, 0 caps fired.
(Re-verified after the tool-manual, parser and prompt fixes and after all 42 transcripts were
re-recorded: the numbers moved, and the sabotage still changes nothing.)

Two consequences, and both belong in the report:

1. **No pass-rate number from the scripted backend can be attributed to failure 2, in either
   direction.** The "unchanged" pass rate in the table above is not evidence the fix is harmless;
   it is evidence the instrument is blind to it. The deterministic evidence for this failure is the
   interface property itself — an excluded line returns `needed_next: []` — plus the guardrail row,
   not the pass rate.
2. **The transcripts must be re-recorded before the battery**, because they were recorded against
   the pre-rewrite descriptors and the pre-rewrite return shape. Until then the scripted backend is
   replaying a conversation the current tool layer would never have produced.
