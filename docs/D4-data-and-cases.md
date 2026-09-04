# D4 · The data — extending it without breaking it

**Owner:** everyone (see [`../PLAN.md` §3](../PLAN.md)) · **Feeds:** report §3

How to write the *cases* is in [`../evaluation/cases/README.md`](../evaluation/cases/README.md).
This file is about the *data underneath them*.

---

## Where the data lives, and why it does not move

```
A2_reference_data/
  make_fixtures_A.py         generator  →  writes data_A/
  check_my_data.py           RUN AFTER EVERY CHANGE
  data_A/                    8 JSON files — the records the tools read
  expected_outcomes_A.json   the answer key — 15 shipped, ours appended
  data_dictionary.json       every field, its type and what it means
```

**Do not move this folder or split it up.** Both scripts anchor on
`os.path.dirname(os.path.abspath(__file__))`, so the generator, the checker, `data_A/` and the
answer key must stay siblings. Split them across `fixtures/` and `evaluation/` and
`check_my_data.py` silently stops finding anything.

We keep the instructor's folder name on purpose: a marker recognises it, and can see at a glance
that we added to it rather than edited it.

---

## The one rule

> ## ADD NEW ROWS WITH NEW IDS. NEVER EDIT OR DELETE A SHIPPED ROW.

Everything else follows from it. A marker re-runs our harness against the original records, and the
shipped answer key is written against them. Change one row and our results stop being comparable
with anyone else's — including our own from last week.

`check_my_data.py` holds a **fingerprint of every shipped row** and will name the one that moved.
This is checked, not trusted.

Two more things in Problem A's neighbours that are protocol, not data: the **routing rule** and the
**gated action**. The answer key is written against both. Tool *names*, by contrast, are only
suggestions — see [`D2-tool-layer.md`](D2-tool-layer.md).

---

## The thing that silently breaks everything

The files connect to one another, and that is how the agent gets from one fact to the next:

```
claims.json ──member_id──► members.json ──policy_id──► policies.json
     │                                                  (status, dates, annual_limit,
     ├──hospital_id──► hospitals.json                    used_to_date, exclusions)
     └──lines[].code──► procedures.json ──requires_preauth──► preauthorisations.json
```

**Invent a claim whose `member_id` matches nobody and the agent will look perfectly sound and
return nothing.** The run completes, the tools return empty, the reasoning is fluent, and the case
is worthless. `check_my_data.py` exists to catch exactly this. Run it after every change.

---

## Cases that need more than one new row

The shipped data has exactly **one** lapsed policy, **one** exclusion rule and **one** true
duplicate. A set built only from new claims keeps re-testing those same three facts, and the
negative cases end up near-clones of each other.

| If you want | You also need |
|---|---|
| a second duplicate-claim case | `EXTRA_DECIDED` — plus a claim matching it on **all four** facts |
| a different exclusion rule | `EXTRA_POLICIES` (new `policy_id`) + `EXTRA_MEMBERS` |
| a second lapsed policy | `EXTRA_POLICIES` + `EXTRA_MEMBERS` |
| a procedure of your own | `EXTRA_PROCEDURES` — you set `requires_preauth` yourself |
| a new document rule | `EXTRA_REQUIRED_DOCS` |

**On duplicates specifically:** all four facts must match — member, hospital, date of service,
lines. The shipped history holds three near-misses that differ on exactly one fact each, so an
agent matching on the date alone, or on member and date, wrongly escalates a claim that is
perfectly fine. If your new pair does not match on all four, it is not a duplicate case.

---

## Before you write a case, check three things

The habit that separates a case that tests what you meant from one that tests something else.
Walk the chain and confirm **nothing earlier fires first**:

1. **Is the policy live on the date of service?** A lapsed policy or a date outside the window
   ends the run — everything downstream is untested.
2. **Does any line hit an exclusion, or need a pre-authorisation?** That changes the outcome and
   the turn count.
3. **Does the claim total fit inside `annual_limit − used_to_date`?** Over the headroom escalates,
   regardless of coverage.

If you want the *duplicate* to be the trigger, none of the three above may fire. If you want the
*limit* to be the trigger, the policy must be live and the lines must be otherwise fine.

---

## Ids

Shipped ids stop well short of ours, deliberately:

| | Shipped | Ours |
|---|---|---|
| Claims | `CLM-8688` … `CLM-8971` | `CLM-9001` upward |
| Members | `M-2214` … `M-6118` | `M-7001` upward |
| Policies | `POL-3310` … `POL-7220` | `POL-8001` upward |

Your personal block inside those ranges is in [`../PLAN.md` §3](../PLAN.md). Stay inside it and two
people can never collide.

> The *Adding extra cases* PDF's worked example uses `CLM-9000` and `CLM-9001`. Do not paste it in
> verbatim — `CLM-9001` belongs to Goncalo's block.

---

## Found a bug in the shipped data?

Email the instructor early — acknowledged bugs earn credit under Class Participation, and a defect
found on 5 September helps 27 other teams while the same defect on the 12th helps nobody. You do
not have to wait for a fix: **say in this repository what you found, what you assumed instead, and
carry on.** A documented workaround is a strong answer, not a compromised one.

| What we found | Where | What we assumed instead | Reported? |
|---|---|---|---|
| — | | | |
