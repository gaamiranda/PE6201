# 2. The tool layer

The agent is a hand-rolled ReAct loop: Thought, an Action block of tool calls, Observations, until a
Final record appears. No framework owns the loop; every turn, token and guard is ours to measure and
defend.

The tool layer is seven functions, and the discipline was *not* adding one.
`check_required_documents` was absorbed into `check_coverage`'s return shape, because both are keyed
on the procedure code — one descriptor fewer per prompt. `lookup_member` we refused: its `join_date`
looks like a coverage date and is not, and `CLM-8917` would have detonated it.

Two signatures make an error unrepresentable, not merely discouraged. `get_preauthorisation`
requires `date_of_service`, so an approval cannot be found without testing whether it applies —
`CLM-8894` is exactly that, an expired pre-authorisation. `check_claim_history` requires all four
match facts together, so a three-fact duplicate match cannot be expressed.

We also overclaimed one: `check_coverage(policy_id, …)` was described as making a wrong
policy-claimant pairing impossible, but the code only validates that the policy id *exists*. We
downgraded it in seven places to what it buys, a visible hop in the evidence trail.

The descriptor rewrite did not pay for itself: the v2 `check_coverage` descriptor grew by about 275
tokens, and re-sent every model call that is +131,216 input tokens across the 76-trial schedule; the
return shape that shipped with it is −1,751. It bought a six-field contract: a size bound on
returns, failure conditions and whether the call is irreversible. We kept it knowing the price.

Calls share a turn only when neither consumes the other's output. `get_claim` runs alone, since
every other tool reads what it returns; `lookup_policy`, `get_hospital_status` and
`check_claim_history` read only the claim row and share the next turn; the per-line `check_coverage`
calls need that turn's `policy_id` but not each other, so several lines cost one turn;
`get_preauthorisation` waits, because which line needs one is unknown until coverage answers.
Grouping by that rule on the same recording took tool-executing turns from 222 to 183, input tokens
from 413,515 to 353,481 and cost from US$0.07103 to US$0.06187, with decisions unchanged at 40/42. A
scheduling choice that changed an answer would be a bug.

One step is irreversible, `issue_decision_letter`, behind an autonomy gate set to `confirm` that
refuses any approval whose record lacks per-line dispositions, a named exclusion for every refusal,
or non-negative integer totals.

<!-- Evidence: ../D2-tool-layer.md (D2(a) the set and the cuts; D2(b) the measured rewrite;
D2(c) the dependency rule and evaluation/d2c_run.json); ../D7-failures.md §Failure 2.3 (the
three-arm split of descriptor and return shape); ../../src/loop.py; ../../src/tools.py. -->
