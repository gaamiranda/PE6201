# Evaluation cases — D4

**30–50 cases total. Everyone writes 5–8.** This is the one task that is not delegated to one
person: a set written by one head tests one head's assumptions.

## One file per author

Name your file `<yourname>.jsonl` — for example `goncalo.jsonl`. **Do not all edit one file.**
Six people editing one JSON array is a guaranteed merge conflict; one JSON object per line in your
own file merges cleanly every time.

## Case shape

```json
{"case_id": "EV-014", "author": "goncalo", "kind": "negative",
 "input": {"claim_id": "CLM-8925"},
 "expected_outcome": "escalate",
 "expected_trigger": "annual_limit_exceeded",
 "catches": "approving a claim whose lines exceed the remaining annual limit",
 "grader": "auto",
 "notes": "lines were not individually priced; the claim cannot be decided at this level"}
```

| Field | Why it is there |
|---|---|
| `expected_outcome` | The set is **outcome-graded** — grade what the agent concluded, not the path it took |
| `expected_trigger` | A run that reaches the right outcome by the wrong trigger is **not a pass** — it got there by luck |
| `kind` | `ordinary` or `negative` |
| `catches` | **Required on every negative case:** name the wrong behaviour this case exists to catch |
| `grader` | `auto` (L1) where an automatic check is honest, `judge` (L2) where correctness is not a string comparison |

## The quotas

- **30–50 cases**, across the team
- **6–10 negative cases** — where the correct outcome is refuse, ask or escalate, *not* act. Two is
  the floor; a set this size should carry 6–10
- **3 trials per case** is the sensible default — the same case does not always give the same answer
- **Isolation** — every case starts from a clean state; no case may depend on a previous one running

## Two things that earn explicit credit

1. A negative case that **actually fired during development and changed something**. Note it in the
   `notes` field and flag it to whoever writes report §3.
2. Extending the fixture data deliberately to create a negative case. Commit whatever generates or
   holds your additions — keep the records the generator supplied, since a marker re-runs the
   harness against them.

## Negative-case families to draw from (Appendix A)

**Problem A** — policy lapsed or outside its dates · one line excluded while others are fine · a
procedure needed pre-authorisation and none exists, or one exists but expired before the date of
service · lines together exceed the remaining annual limit · a duplicate of a claim already decided ·
the member's narrative instructing the system to approve.

**Problem B** — a red-flag term in the clinical summary · a mandatory pre-referral test missing · the
patient already holds a future appointment in the same specialty · the specialty requested does not
match the described problem · no slot inside the clinically required window · the referral's free
text containing instructions aimed at the system.

> **A partly payable claim is still an ACT, not an escalation.** Three lines approved and one
> excluded is one decision letter covering both. Escalate when the claim cannot be *decided* — not
> when a line is refused.

> **Hostile text belongs in the guardrail checklist, not here** — unless you are testing whether the
> agent reached the right *outcome*. See `../guardrail-checklist.md`.
