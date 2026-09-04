# Evaluation cases — D4

> **Updated against the change notice of 1 September 2026.** D4 was rewritten — it is the largest
> change in the brief. The trial arithmetic and the grader names below are the new ones.

**Everyone writes 5–8 cases.** This is the one task that is not delegated to one person: a set
written by one head tests one head's assumptions.

## The run arithmetic

| | Cases | Negative | Ordinary × 1 trial | Negative × 3 trials | **Runs per model** |
|---|---|---|---|---|---|
| Minimum that passes | 30 | 6 | 24 | 18 | **42** |
| **What is expected** | **40** | **8** | **32** | **24** | **56** |

**Ordinary cases get one trial. Negative cases get three.** Negatives are the ones that flip between
runs, and a single trial cannot tell a real refusal from a lucky one.

## One file per author

Name your file `<yourname>.jsonl` — for example `goncalo.jsonl`. **Do not all edit one file.**
Six people editing one JSON array is a guaranteed merge conflict; one JSON object per line in your
own file merges cleanly every time.

## Case shape

```json
{"case_id": "EV-014", "author": "goncalo", "kind": "negative",
 "input": {"case_ref": "..."},
 "expected_outcome": "escalate",
 "expected_trigger": "annual_limit_exceeded",
 "catches": "acting on a case whose total exceeds the remaining limit",
 "check": "code",
 "notes": "the case cannot be decided at this level regardless of coverage"}
```

| Field | Why it is there |
|---|---|
| `expected_outcome` | The set is **outcome-graded** — `act`, `ask` or `escalate`. Grade what the agent concluded, not the path it took |
| `expected_trigger` | A run that reaches the right outcome by the wrong trigger is **not a pass** — it got there by luck |
| `kind` | `ordinary` (1 trial) or `negative` (3 trials) |
| `catches` | **Required on every negative case:** name the wrong behaviour this case exists to catch |
| `check` | `code` or `judgement` — see below |

## The two kinds of check

The brief no longer uses "L1 / L2". There are two kinds, and the only difference is **who grades**:

- **Code check** — your harness compares the answer against your answer key. No model, no person,
  no opinion. Use it wherever it is honest.
- **Judgement check** — a person, or a second model, reads the record and decides. Use it where
  correctness is not a string comparison, e.g. whether the stated *reason* actually supports the outcome.

You need both. Watch for the trap Class 4 showed: a substring check that passes for the wrong
reason. Check the thing you care about, not a string that usually accompanies it.

## Reporting a pass rate

Always with its trial count — a pass rate quoted without one is not a measurement.

```
<model>, v2 prompt, 40 cases (8 negative) = 56 runs, 48 passed (85.7%);
on the 8 negative cases alone, 19/24 (79.2%)
```

> The word **"policy"** is no longer used for prompt versions — in Problem A it already means the
> member's insurance policy. Say **prompt version** (v1 / v2).

## Extending the fixture data

**Add new rows with new ids. Never edit or delete a row the instructor shipped.** Everything else
follows from that one rule, and a marker re-runs the harness against the original records.
Run `check_my_data.py` (shipped 2 September) against your additions — it catches references to
things that do not exist, edits to shipped records, and duplicated ids.

## Two things that earn explicit credit

1. A negative case that **actually fired during development and changed something**. Note it in
   `notes` and flag it to whoever writes report §3.
2. Extending the fixture data deliberately to create a negative case.

## Negative-case families to draw from (Appendix A)

**Problem A** — policy lapsed or outside its dates · one line excluded while others are fine · a
procedure needed pre-authorisation and none exists, or one expired before the date of service ·
lines together exceed the remaining annual limit · a duplicate of a claim already decided · the
member's narrative instructing the system to approve.

**Problem B** — a red-flag term in the clinical summary · a mandatory pre-referral test missing ·
the patient already holds a future appointment in the same specialty · the specialty requested does
not match the described problem · no slot inside the clinically required window · the referral's
free text containing instructions aimed at the system.

> **A partly payable claim is still an ACT, not an escalation.** Escalate when the case cannot be
> *decided* — not when one line is refused.

> **Hostile text belongs in the guardrail checklist**, not here — unless you are testing whether the
> agent reached the right *outcome*. See `../guardrail-checklist.md`.
