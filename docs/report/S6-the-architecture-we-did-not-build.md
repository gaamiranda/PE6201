# 6. What we would not deploy

We would not deploy this unattended; the limits are ours. The guardrail checklist is 9/10 under every arm, always failing `CLM-8952`, where the injection imitates a tool result. Injection resistance is model-dependent; DeepSeek catches one of three. Before the write, `unsupported()` checks structural preconditions only, not every recorded fact, and can be overridden. Correct decisions arrive with records that cannot justify them: 72 of 76 scripted trials reached the expected decision, 63 passed the code check, 57 the combined check; six failed only on human judgement.

Those six make a read-only reviewer plausible; we did not build one because its value was unmeasured, not disproven. The Cognition papers back a clean-context reviewer if writes stay single-threaded; ours has one writer. We would add one after a paired test on the same cases measuring combined pass rate, false escalations, tokens, latency and human-review cost; it could advise or veto, never write.

<!-- Evidence: ../../results/evaluations/eval-scripted-v2-final.summary.json (72/76 decision-only,
63/76 code-only, 57/76 combined; 6 trials pass every code check and fail on human judgement);
../D7-failures.md §Failure 2.3 (guardrail checklist 9/10 under every arm, row 2 `CLM-8952`);
../../src/loop.py (`unsupported()`); Cognition, "Don't Build Multi-Agents" and "Multi-Agents:
What's Actually Working" (Pre-read 5); ../D0-why-an-agent.md D0(a) §4. -->
