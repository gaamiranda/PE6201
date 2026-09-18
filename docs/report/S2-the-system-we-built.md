# §2 · The system we built

**Owner:** Goncalo Miranda · **Budget:** 300 words · **Evidence:** `docs/D2-tool-layer.md`, `src/loop.py`, `src/tools.py`

---

The agent is a hand-rolled ReAct loop. The model emits a Thought and an Action block of one or
more tool calls; the loop executes them, returns Observations, and repeats until a Final record
appears. No framework owns the loop, so every turn, token and guard is ours to measure and defend.

The tool layer is seven functions, and the discipline was to try *not* to add one. Two candidates
never shipped. `check_required_documents` was absorbed into `check_coverage`'s return shape,
because both are keyed on the procedure code — one fewer descriptor in every prompt, at zero extra
calls. `lookup_member` we refused outright. It would return `join_date`, which looks like a
coverage date and is not; the data dictionary says so in as many words. Handing a model both dates
is a landmine, not a fact, and `CLM-8917` is the case that would have detonated it.

Two signatures make an error unrepresentable rather than merely discouraged.
`get_preauthorisation` requires `date_of_service`, so an approval cannot be found without testing
whether it applies — `CLM-8894` is exactly that, a pre-authorisation that exists and expired.
`check_claim_history` requires all four match facts together, so a three-fact duplicate match
cannot be expressed; the fixtures ship three near-misses that punish any shortcut.

We also overclaimed one, and the correction matters more than the claim did. We had described
`check_coverage(policy_id, …)` as making a wrong policy-claimant pairing impossible. Reading the
document against the code showed it only validates that the policy id *exists*. We downgraded it
in seven places to what it actually buys: a visible hop in the evidence trail.

One step is irreversible — `issue_decision_letter` — and it sits behind an autonomy gate set to
`confirm`. The gate refuses any approval whose record lacks per-line dispositions, a named
exclusion for every refusal, or non-negative integer totals.
