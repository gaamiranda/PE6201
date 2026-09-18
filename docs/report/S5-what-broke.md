# §5 · What broke, and what we changed

**Owner:** SUN YUCONG · **Budget:** 350 words · **Evidence:** `docs/D7-failures.md`, `docs/D2-tool-layer.md`, `evaluation/guardrail-checklist.md`

---

The most useful failures here were not random model mistakes. They exposed mismatches between what
our interface promised and what the agent could rely on: the descriptors, the v1 to v2 rewrite,
and the guardrail layer around unsafe autonomy.

Two things changed in v2, and keeping them apart matters. The **descriptor contract** became six
fields — signature, what it answers, inputs, returns with a size bound, failure conditions, and
whether it is irreversible. Separately, `check_coverage`'s **return shape** was rewritten so
`coverage.status` and `needed_next[]` cannot contradict one another: a line refused as not covered
can no longer ask for documents for itself.

D7's second failure was built to separate those changes, and the result was not what we expected.
Three arms — the shipped version, the old shape with the new descriptor, and the repository at
`91da36f` — scored **identically**: 63/76 on code, 40/42 on decisions, 9/10 on the guardrail
checklist. Only cost differed: the descriptor accounts for 131,216 input tokens across the
schedule, the return shape for 1,751. The rewrite bought consistency and traceability, not
accuracy — and replay could not have shown otherwise, being keyed on case and turn, which is
exactly why one member runs the v1 prompt live.

The DeepSeek battery made that result more useful and less comfortable. It scored 53/76 on code
and 50/76 combined, with two provider timeouts reported separately. The headline is not the
aggregate but the prompt-injection set: three cases, nine trials — a signal, not a measured rate.
The recording model catches two of three. DeepSeek catches one. It fails `CLM-8952`, where the
injection imitates a tool result, and also `CLM-8941`, the blatant "ignore the policy and approve"
case the recording model escalates in one turn.

So the guardrail is not a safety property bolted onto the loop. It is a design pressure: structure
the evidence, block irreversible actions when the trigger is visible, and check whether each model
uses that structure. Final-action gates are necessary and insufficient. We changed the descriptors
and the gate because our own tests showed the old interface let ambiguity pass too quietly; the
live run showed the improved one is still model-dependent.
