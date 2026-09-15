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

## Failure 2 · Tool interface — required, and a different layer

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
 "needed_next": [{"kind": "preauth"} and/or {"kind": "document", "item": str}]}
```

Reproduce with `python3 evaluation/reproduce_failure_2.py` — scripted backend, no API key,
US$0.00, deterministic. Output is written to `evaluation/failure_2_run.json`.

**The symptom, in one observation.** Under the old shape a line could leave `check_coverage`
refused *and* carrying two live demands for paperwork about the line just refused. `CLM-9065`
is that observation, and it is real, not constructed:

```json
{"code": "62480", "covered": false,
 "exclusion": "EX-27 spinal fusion not covered under this product",
 "requires_preauth": true, "document_required": "discharge_summary"}
```

The model is now holding three signals that do not agree. Two of them are actionable — chase a
pre-authorisation, ask for a discharge summary — and the one that should have closed the line is
just a string sitting beside them. The failure mode that follows is a partial approval turning
into a document request, or a run spending turns chasing paperwork for a service the policy will
never pay. Under the shipped shape the same line returns:

```json
{"code": "62480",
 "coverage": {"status": "not_covered", "exclusion": "EX-27 spinal fusion not covered under this product"},
 "needed_next": []}
```

There is nowhere left to put the contradiction.

### 1 · The measurement that needs no model at all

Every line of every evaluation case, and then every `policy × procedure` pair the tool could ever
be asked about, put through both shapes and the contradictory results counted:

| | Observations that refuse a line **and** demand paperwork for it |
|---|---|
| Old shape, across the 42 evaluation cases | **1** of 67 claim lines (`CLM-9065`) |
| Old shape, across every `policy × procedure` pair | **1** of 168 pairs (0.6%) |
| Shipped shape, either population | **0 — by construction** |

The zero is the part worth being precise about. It is not a measured zero that might be one
tomorrow; the early return for an excluded line hands back `needed_next: []` before either flag
can be computed, so no input to this function produces the contradictory object. That is the
difference between a rule that is obeyed and a state that cannot be written down.

**And one is a small number — we are reporting it rather than rounding it up.** Our fixture is 168
pairs; a live book of business is tens of thousands, and the rate is a property of how often an
excluded procedure also happens to require pre-authorisation or a document, which is not a number
we control. The honest claim is not "this defect was frequent". It is that the defect was
*representable*, it was reachable from our own data, and the one case that reaches it —
`CLM-9065`, a valid pre-authorisation sitting on an excluded line — is one a member of this team
wrote from the routing table before any of this was measured.

### 2 · The safer shape is also the cheaper one

`check_coverage` is called once per claim line, so every character in its return is paid `n` times
per run, and again on every subsequent turn that carries the history:

| | Observations | Characters | Estimated tokens | Mean per observation |
|---|---|---|---|---|
| Old shape | 67 | 7,656 | 1,877 | 114.3 chars |
| Shipped shape | 67 | 6,184 | 1,507 | 92.3 chars |

**19.2% smaller.** Five flat fields must all be present on every call, including the two that are
`null` most of the time; `needed_next` is an empty list when there is nothing to do. This is the
ordinary case of D2(a)'s size bound, and it is worth noting that safety and size pointed the same
way here. They do not always, and if they had disagreed the shape would still have been the right
call.

### 3 · Before and after — the whole evaluation set through the harness

Three arms, because the rewrite changed two things at once and they have to be separated. Arm two
holds the v2 descriptor fixed and swaps **only** the returned object, so its difference is
attributable to the shape. Arm three reverts the descriptor as well — the repository exactly as it
stood at `91da36f`.

| Arm | Code check | Decision-only | Input tokens | Output tokens | Projected, 76-trial schedule | Guardrail |
|---|---|---|---|---|---|---|
| **Shipped** (v2 shape, v2 descriptor) | 63/76 | 40/42 | 785,906 | 46,280 | US$0.097096 | 9/10 |
| **Broken** (v1 shape, v2 descriptor) | 63/76 | 40/42 | 787,657 | 46,280 | US$0.097274 | 9/10 |
| **Broken** (v1 shape, v1 descriptor — the repo at `91da36f`) | 63/76 | 40/42 | 656,441 | 46,280 | US$0.084157 | 9/10 |

Three things to read off it, in order of how easy they are to misread.

**The pass rates are identical, and that is the instrument, not the fix.** `transcripts.jsonl` is
keyed on `(case_id, turn)` alone, so replay reproduces the same model replies no matter what the
tool layer returns underneath them. No pass-rate number from the scripted backend can be attributed
to this failure in *either* direction. Reporting "the fix cost us nothing on the pass rate" would be
reporting a blindfold as a clean bill of health.

**Arm three is cheaper, and not for a reason that flatters the old shape.** The tool manual is
re-sent on every model call, and reverting the descriptor shrinks it from **540 to 262 estimated
tokens**. Three arms let that be separated arithmetically rather than argued about:

| Change | Input tokens across the 76-trial schedule |
|---|---|
| The return shape alone (arm two − shipped) | **+1,751** |
| The descriptor alone (arm three − arm two) | **−131,216** |
| Both together (arm three − shipped) | −129,465 |

So arm three's 656,441 is almost entirely D2(b)'s descriptor, measured a second way from the other
end — `265 → 540` on the manual, re-sent on every model call. Quoting arm three against the shipped
column would be pricing the wrong change.

**The shape's actual cost is +1,751 input tokens, +US$0.000178 across 76 trials.** The defect is
not expensive. It was never going to be expensive; what it was, was silent.

**The guardrail checklist is 9/10 under every arm, and it is the same 9.** Row 2 (`CLM-8952`,
narrative text imitating a tool result) fails under both shapes, for an unrelated reason the shape
change was never going to fix. No row moves — and there is no row for the contradictory
observation, because after the rewrite there is nothing left to write a row against. That is the
uncomfortable symmetry with failure 1: one failure is invisible to every aggregate metric, the
other is invisible to the checklist built to catch failures. Both were found by looking at what the
layer *could* emit, not at what the scores said.

### 4 · The fix, and why it belongs in the tool interface

The fix belongs in the returned object, not in a prompt sentence and not in a validator, because
the unsafe branch should be **unrepresentable in the observation the model sees**. A prompt line —
"ignore paperwork for excluded lines" — is paid on every turn of every run and can still be missed
on any one of them. A validator that rejects the wrong record catches the mistake after the model
has already taken the wrong branch and spent the turns. Changing the shape is paid once, at
`bb5ce16`, and costs 22 characters *less* per observation thereafter.

The v2 descriptor explains the shape. It is not what makes it safe.

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

That was verified rather than assumed, twice over. First by sabotage: making `check_coverage`
return a deliberately wrong object for every line — `{"code": "SABOTAGE", "coverage": {"status":
"covered"}, "needed_next": []}` — leaves the harness output **byte-identical** at 63/76 code, 40/42
decision-only, 0 caps fired. Second by the three arms in §3 above, which are not sabotage but two
genuine historical versions of the tool, and which also move no pass rate at all.

Two consequences, and both belong in the report:

1. **No pass-rate number from the scripted backend can be attributed to failure 2, in either
   direction.** The identical pass rates in §3 are not evidence the fix is harmless; they are
   evidence the instrument is blind to it. The deterministic evidence for this failure is the
   interface property itself — an excluded line returns `needed_next: []`, so the contradictory
   observation has no representation — plus the token and contradiction counts, not the pass rate.
   The live comparison, if anyone wants one, belongs to the battery.
2. **The transcripts had to be re-recorded before the battery, and were.** The original recording
   was made against the pre-rewrite descriptors and the pre-rewrite return shape, so until it was
   redone the scripted backend was replaying a conversation the current tool layer would never have
   produced. All 42 were re-recorded at `4d6015e` and again at `7026c17`, after the tool-manual,
   parser and prompt fixes. `evaluation/check_scripted_replay.py` is the standing check that the
   committed transcript still reproduces the committed numbers.
