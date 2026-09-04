# D3 · The guardrail layer

**Owner:** [name] · **Criteria:** Technical Execution + Conceptual Understanding

> Two different things. (a) is code, shipped *before* any prompt tuning. (b) is a test checklist,
> and it is **not** the evaluation set.

---

## (a) The code layer

| Guard | Value | Where the number came from |
|---|---|---|
| Step cap | | measured worst legitimate run = [n], so cap = [n+1]. Not a round number. |
| Budget ceiling | | |
| Action de-duplication | | |
| Monthly limit per user | | |

**Autonomy setting:** `[suggest / confirm / act]`

The gate sits in front of **[the irreversible step]**, not in front of the agent as a whole.

**Why this setting:** [defend it against the irreversible step, not by taste. For Problem B in
particular: acting is the dangerous outcome, so say how that asymmetry shaped this choice.]

**The stop is loud:** [how a cap announces itself — a cap that silently returns an empty answer is
worse than the loop, because it converts a visible cost problem into an invisible correctness one.]

---

## (b) The guardrail checklist

Lives in [`../evaluation/guardrail-checklist.md`](../evaluation/guardrail-checklist.md).

> **Run all ten on the scripted backend** (change notice, 1 Sep). A step cap, a budget ceiling,
> de-duplication and the autonomy gate are all *our* code — a model cannot influence whether they
> fire — so a deterministic backend is the **correct** instrument, not merely the cheap one. These
> ten cases cost nothing and need no API key.
>
> **The caveat, and it belongs in the report:** a scripted run proves the guardrail fires when the
> agent *attempts* a bad action. It cannot tell us whether a live model can be talked into
> attempting it. That second question belongs to the D5 battery, not to a guardrail case.

At least **10 cases**, each naming the wrong behaviour it exists to catch and stating the observed
result. **At least 3** must cover the request text itself being hostile — both problems contain free
text written by someone outside the organisation.

> Do not file hostile-input tests as evaluation cases. A team that does has a 40-case eval set and
> an empty checklist, and the brief marks the distinction.
