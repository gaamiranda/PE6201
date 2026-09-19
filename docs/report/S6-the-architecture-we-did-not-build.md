# 6. The architecture we did not build

Correct decisions with records that cannot justify them make a read-only reviewer plausible, but they do not show that it would pay. In the scripted schedule, 72 of 76 trials reached the expected decision, 63 passed the code check, and 57 passed the combined standard. This decomposition matters: some losses arose before human judgement, from routing, document-containment or validator failures; six further trials failed judgement. A reviewer given the narrative, tool observations and proposed record might catch omissions, but we ran no reviewer ablation, so its gain, false-veto rate and correlated errors remain unknown.

The two Cognition papers provide design precedent, not evidence from insurance claims. “Don’t Build Multi-Agents” warns that fragmented context and the implicit decisions carried by parallel writers produce inconsistent results. “Multi-Agents: What’s Actually Working” narrows that warning: clean-context reviewers can contribute intelligence, provided writes remain single-threaded. The later paper therefore supports testing a reviewer, while still arguing against parallel authority.

Our independent retrieval work is already batched as tool calls, and the system has one consequential write, issue_decision_letter. Before that write, unsupported() checks limited structural and tool-call preconditions; it does not verify every recorded fact and can be overridden. We therefore retained one bounded loop and one writer, not because multi-agent review was disproven, but because its value was unmeasured. We would add a read-only reviewer only after a paired test on the same model and cases, measuring combined pass rate, false escalations, tokens, latency and downstream human-review cost. Any reviewer could advise or veto; the final write would remain serial.

<!-- Evidence: ../../results/evaluations/eval-scripted-v2-final.summary.json (72/76 decision-only,
63/76 code-only, 57/76 combined; 6 trials pass every code check and fail on human judgement);
../../src/loop.py (`unsupported()`); Cognition, "Don't Build Multi-Agents" and "Multi-Agents:
What's Actually Working" (Pre-read 5); ../D0-why-an-agent.md D0(a) §4. -->
