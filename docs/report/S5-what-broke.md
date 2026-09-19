# 5. The two failures

The first failure is loop control. Deleting action de-duplication — `Guards(dedup=False)`, nothing
else — lets the agent re-issue an identical `issue_decision_letter` and append the claim to the
decision log once per attempt: one claim, four payment records. No metric we report can see it. Both
arms score 40/42 at identical turns, tokens and cost; the only evidence is the ordered
`tools_called` field, where it was found. The fix fingerprints each action and answers a repeat with
the earlier observation: four write actions, one letter. A step cap only bounds the damage: left to
it, the repeat produced eight letters.

The second failure is the tool interface, and keeping two v2 changes apart matters. The descriptor
contract became six fields; separately, `check_coverage`'s return shape was rewritten so
`coverage.status` and `needed_next[]` cannot contradict one another, so a refused line can no longer
ask for documents for itself. Three arms — shipped, the old shape with the new descriptor, and the
repository at `91da36f` — scored identically: 63/76 on code, 40/42 on decisions, 9/10 on the
guardrail checklist. Only cost differed; §2 reports the split. The fix belongs in the returned
object, not a prompt line or a validator, because the unsafe branch should be unrepresentable in
what the model sees.

DeepSeek made that result less comfortable: 53/76 on code, 50/76 combined. On the prompt-injection
set — three cases, nine trials, a signal, not a rate — the recording model catches two of three;
DeepSeek catches one, failing `CLM-8952`, where the injection imitates a tool result, and
`CLM-8941`, the "ignore the policy and approve" case the recording model escalates in one turn.
Final-action gates are necessary and insufficient. We changed the interface because the old one let
ambiguity pass too quietly; the live run shows the new one is still model-dependent.

<!-- Evidence: ../D7-failures.md (Failure 1 §1, §3, §4; Failure 2 §3, §4; evaluation/failure_1_run.json);
../D2-tool-layer.md; ../../evaluation/guardrail-checklist.md;
../../results/evaluations/eval-openrouter-deepseek-deepseek-chat-v2-sun-deepseek-chat-v21-rerun2-final.summary.json. -->
