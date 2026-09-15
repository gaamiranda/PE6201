# D3 · The guardrail layer

**Owner:** SUN YUCONG · **Criteria:** Technical Execution + Conceptual Understanding

*Deadlines and dependencies: [`../PLAN.md`](../PLAN.md).*

> Two different things. (a) is code, shipped *before* any prompt tuning. (b) is a test checklist,
> and it is **not** the evaluation set.

---

## (a) The code layer

| Guard | Value | Where the number came from |
|---|---|---|
| Step cap | `12` tool-executing turns | Measured distribution with caps lifted: median 6, p90 7, max 10. Cap 12 clears the longest legitimate run by 2 turns and is 1.7x p90. |
| Call cap | `18` model calls | Measured distribution: median 8, p90 10.5, max 14. Cap 18 clears the max by 4 calls and catches no-action loops that do not advance the step counter. |
| Budget ceiling | `US$0.0044` projected per run | Recomputed after the D2(b) descriptor rewrite over the committed 76-trial scripted baseline: median US$0.001731, p90 US$0.002689, max US$0.004272 (`CLM-9005`). Ceiling US$0.0044 clears max by US$0.000128 (3.0%). |
| Action de-duplication | On | The loop fingerprints tool name, args and kwargs. A repeat returns the earlier observation instead of executing the action again, so a repeated write cannot append twice. |
| Monthly limit per user | Outside this repo | This student harness has no identity or billing account boundary. The production control belongs at the OpenRouter/account layer; this repo records per-run cost so that layer has an enforceable number. |

**Autonomy setting:** `confirm`

The gate sits in front of **`issue_decision_letter`**, the irreversible append to
`results/decisions.jsonl`, not in front of the agent as a whole.

**Why this setting:** Problem A's ordinary successful outcome is the dangerous action: an
approval letter creates a business commitment, while `request_document` and `escalate` do not
write a decision letter. `suggest` is too weak for the assignment because it never exercises the
gated action we are required to build and measure. `act` is too strong because it lets a model
append an approval with no operator checkpoint. `confirm` is the middle setting the system should
ship with: the agent may investigate and assemble a record, but the irreversible write opens only
after the loop's evidence precondition and `_gate_open()`'s structural confirmation both pass. In
the offline harness that confirmation is deterministic; in production the final gate reason would
be replaced by a human approval event.

**The stop is loud:** a cap sets `usage["cap_fired"]`, changes the record to an escalation, and
writes a reason beginning `STOPPED BY GUARDRAIL`. It does not return an empty record or a pretend
approval. A cap that silently returns nothing converts a visible cost problem into an invisible
correctness problem; this one leaves the failure in the harness output.

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
