# Evaluation cases — D4

**Read [`../../PLAN.md` §3](../../PLAN.md) first** — it has your id block and your place in the baton.

---

## There is ONE answer key, and it is not in this folder

> *"There is one answer key per problem, and it grows. You do not start a second file."*
> — A2 · Adding extra cases, §7

The ground truth for every case — the 15 shipped and the 25 we write — is:

```
A2_reference_data/expected_outcomes_A.json
```

It starts as 15 labelled records and ends as 40. `check_my_data.py` scores against it. The harness
joins on `case_id` and does not care which rows are the instructor's and which are ours.

**This folder holds no case data.** An earlier version of this README told you to write
`<yourname>.jsonl` files here. That was wrong: a second key is invisible to `check_my_data.py`,
and the shipped key is a **submitted artefact** in its own right. If you have a `.jsonl` file here,
fold it into `expected_outcomes_A.json` and delete it.

---

## Two files, two edits, per case

Every case you write is **two** edits, and neither is optional.

| | File | What goes in | Automated? |
|---|---|---|---|
| 1 | `A2_reference_data/make_fixtures_A.py` | The **record** — a claim, plus any supporting rows it needs | you edit the `EXTRA_*` lists, then run the generator |
| 2 | `A2_reference_data/expected_outcomes_A.json` | The **label** — what the correct answer is | **by hand. Nothing can do this for you.** |

A script that could work out the right answer would be the agent we are being asked to build.

---

## The loop

```bash
git pull                          # ALWAYS first — we work one at a time

# 1 · open A2_reference_data/make_fixtures_A.py
#     search for  EXTRA_PROCEDURES  — about 40 lines from the bottom
#     that block of empty lists is the ONLY part of the file you touch.
#     Everything above it is shipped data. Scrolling up to edit is the one thing forbidden.

# 2 · add your rows, using ids from YOUR block in PLAN.md §3

# 3 · regenerate
cd A2_reference_data
python3 make_fixtures_A.py

# 4 · check
python3 check_my_data.py
#     FAIL  CLM-9001 has no label in expected_outcomes_A.json — it cannot be scored.

# 5 · add the label BY HAND to expected_outcomes_A.json, then check again
python3 check_my_data.py
#     Your data hangs together.

git add -A && git commit -m "eval cases: <your name>, CLM-90xx..90yy" && git push
# then tell the next person on the baton
```

**Do not push a failing checker.** It fails for the whole team.

The checker catches four things, all of them silent if you do not look: an id that resolves to
nothing (a claim whose `member_id` matches nobody — the most expensive mistake available here);
a shipped record that changed; a duplicate id; a case with no label or a label with no case.

---

## The shape of a label

```json
{ "case_id": "CLM-9001",
  "expected_decision": "escalate",
  "trigger": "duplicate_claim",
  "family": "duplicate_of_decided_claim",
  "must_record": ["CLM-9000 named as the prior decision",
                  "the facts that matched: member, hospital, date of service, lines"],
  "note": "Our second duplicate. M-6118 rather than M-2214." }
```

| Field | When | What |
|---|---|---|
| `case_id` | always | joins to `claim_id` |
| `expected_decision` | always | `approve_in_principle` · `request_document` · `escalate` |
| `trigger` | escalations only | the **one** reason |
| `missing` | requests only | the **one** named thing |
| `family` | always | which case family this exercises |
| `must_record` | always | what a full-marks decision record carries beyond the decision |
| `note` | always | why this case exists — write it while you still remember |

---

## Where the label comes from — the routing table, not your agent

The label is **read off the routing table in Appendix A of the brief**. Find the row whose
situation your record matches. That row gives you two things: the *Outcome* column is your
`expected_decision`, and the *What the record must carry* column is your `must_record` (and, for
an escalation, the single trigger it names; for a request, the exact missing thing).

| The situation | Outcome |
|---|---|
| Every line resolves — covered, covered once a valid pre-auth is found, or clearly excluded | `approve_in_principle` |
| A line needs pre-authorisation and none exists, or one expired before the date of service | `request_document` |
| A required document is absent — itemised bill, discharge summary | `request_document` |
| Policy lapsed or outside its dates · lines together exceed the remaining annual limit · duplicate of a decided claim · the narrative contains instructions aimed at the system | `escalate` |

**If your record matches two rows, or none, the case is not ready.** Two rows means it is
ambiguous — split it. No rows means you invented a situation the protocol does not cover —
interesting, but ungradeable. Fix the record, never the rule.

> ### Write the label BEFORE you run the agent
>
> This is the one that quietly ruins evaluation sets. It is tempting to write the record, run the
> agent, see what comes out and put that in the key. **A key written from the agent's output
> measures nothing** — the agent agrees with itself by construction, the pass rate goes to 100%,
> and we have built an expensive way to learn what we already knew.
>
> When the agent later disagrees with your key, that is the finding. Sometimes the agent is wrong
> and the case has earned its keep. Sometimes the label was wrong — fixing it is good practice, not
> cheating. **The test that separates the two:** could you justify the label to someone who had
> never seen the agent's output, using only the routing table? If yes, fix the label. If no, the
> agent is what is wrong.

---

## What to write — plan before you type

Twenty variations on the same easy claim measure nothing. **15 shipped cases already cover these
families**, so check before you duplicate one:

| Already shipped | Cases |
|---|---|
| approve — partly payable, short run, valid pre-auth, non-panel, four-line long run, near-limit | 6 |
| request_document — pre-auth absent, pre-auth expired, required document absent | 3 |
| escalate — policy lapsed, outside dates, annual limit, duplicate, 2× narrative injection | 6 |

For the 25 we add, aim for this spread:

| Kind of case | Aim for | Example |
|---|---|---|
| The ordinary act | 8–10 | a covered claim, one or two lines, live policy |
| Length variation — same outcome, different run length | 3–4 | one line vs four; with and without a pre-auth chase |
| Boundary — just inside, just outside | 3–4 | exactly at the remaining limit, and a dollar over |
| The named ask | 3–4 | a required document not attached |
| Escalate — the rule | 2–3 | lapsed policy · outside dates · over the limit |
| Escalate — the history | 1–2 | a duplicate of a decided claim |
| Escalate — hostile text | 1–2 | a narrative instructing the system to approve |

**Some cases need more than one new row.** The shipped data has exactly one lapsed policy, one
exclusion rule and one true duplicate — a set built only from new claims keeps re-testing the same
three facts. See [`../../docs/D4-data-and-cases.md`](../../docs/D4-data-and-cases.md).

---

## Negative cases

A **negative case** is one whose correct outcome is the *ask* or the *escalate* — anything except
the act. Two things earn explicit credit:

1. A negative case that **actually fired during development and changed something**. Say so in
   `note` and tell whoever writes report §3.
2. **Extending the fixture data deliberately** to create a negative case.

> **A partly payable claim is still an ACT, not an escalation.** Three lines approved and one
> excluded is one decision letter covering both. Escalate when the claim cannot be *decided* — not
> when a line is refused.

> **Hostile text belongs in the guardrail checklist**, not here — unless what you are testing is
> whether the agent reached the right *outcome*. The two shipped injection cases (`CLM-8941`,
> `CLM-8952`) are evaluation cases because they test the outcome. A case testing whether the gate
> *blocked* something goes in [`../guardrail-checklist.md`](../guardrail-checklist.md).

---

## How the harness grades — two kinds of check, and we need both

| | Code check | Judgement check |
|---|---|---|
| Who grades | the harness, against the key | a person on the team, or a second model |
| Use it for | the decision · the trigger · the named missing item · whether the gated action fired exactly once | whether the stated reason is actually a reason; whether the evidence trail supports the decision |
| Costs | nothing, same result every time | a person's time, or tokens |

**Decided by the field, not by taste.** A field whose value comes from a fixed list is a code
check, always. A field written in prose is a judgement check. Most of the set is code-checked.
Say which, per case, in the results table.

If a model grades, **name it, commit the grading prompt, and use a different model from the one
being graded.** An undocumented judge is not a measurement.

Watch the trap Class 4 showed: a substring check that passes for the wrong reason. Check the thing
you care about, not a string that usually accompanies it.

---

## Trials, and reporting a pass rate

**Ordinary cases get 1 trial. Negative cases get 3** — they are the ones that flip, and one trial
cannot tell a real refusal from a lucky one.

A run that reaches the right outcome by the **wrong trigger is not a pass**. It got there by luck
and it will not get there next time.

Always quote the trial count. A pass rate without one is not a measurement:

```
<model>, v2 prompt, 40 cases (10 negative) = 60 runs, 51 passed (85.0%);
on the 10 negative cases alone, 24/30 (80.0%)
```

> Say **prompt version** (v1 / v2), never "policy" — in Problem A that word already means the
> member's insurance policy.
