## 3. Evaluation and Results

We evaluated one frozen set of 42 claims: 25 ordinary cases were run once and 17 negative cases three times, giving 76 scheduled trials per model. The harness deliberately separates three questions. A decision-only check asks whether the routing outcome is correct. The deterministic code check additionally verifies the required trigger or requested-document containment and rejects validator overrides or unresolved gaps. Finally, six designated cases (12 weighted trials) require human judgement of whether every `must_record` fact appears anywhere in the complete structured final record; hidden Thought text and fixture facts do not count. A trial passes finally only when both applicable checks pass.

This distinction materially changes the result. The free scripted-v2 baseline chose the expected decision in 40/42 unique cases (95.24%; 72/76 weighted trials), but passed 63/76 code checks and 57/76 combined checks (75.00%). Its negative result was 36/51 (70.59%). Thus decision accuracy alone overstated deployable, auditable performance. The judgement workflow remained reproducible: each verdict was joined by stable model, prompt, case and trial identifiers, while blank queues, completed reviews and applied-judgement audits were retained separately.

| Owner | Live battery | Code-only | Final combined | Negative final | Errors / caps |
|---|---|---:|---:|---:|---:|
| Goncalo | GPT-4o-mini, v2 | 32/76 (42.11%) | 31/76 (40.79%) | 21/51 (41.18%) | 0 / 12 |
| Jin | Gemini 2.5 Flash Lite, v2 | 64/76 (84.21%) | 58/76 (76.32%) | 37/51 (72.55%) | 0 / 0 |
| Niu | Llama 3.3 70B, v2 | 45/76 (59.21%) | 42/76 (55.26%) | 20/51 (39.22%) | 0 / 0 |
| Sun | DeepSeek Chat, v2 | 53/76 (69.74%) | 50/76 (65.79%) | 31/51 (60.78%) | 2 / 0 |
| Wang | Mistral Medium 3, v2 | 58/76 (76.32%) | 53/76 (69.74%) | 31/51 (60.78%) | 0 / 0 |
| Zheng | GPT-4o-mini, v1 | 28/76 (36.84%) | 28/76 (36.84%) | 19/51 (37.25%) | 0 / 10 |

Across the live batteries, Gemini 2.5 Flash Lite was strongest at 58/76 combined (76.32%) and was only one trial above its scripted replay, supporting record-and-replay as a useful low-cost regression method. Mistral followed at 53/76, DeepSeek at 50/76, Llama at 42/76, GPT-4o-mini v2 at 31/76, and GPT-4o-mini v1 at 28/76. The controlled GPT comparison therefore favoured v2 by only three trials, while both versions still encountered call-cap failures. Llama completed all 76 trials without runtime errors or caps, but its 36/42 decision-only case score fell to 42/76 combined, showing that correct routing often lacked the structured evidence required for audit.

Negative cases were the clearest discriminator: final negative pass rates ranged from 37.25% to 72.55%. DeepSeek’s two provider timeouts are reported separately from semantic failures; Mistral’s zero-error battery ran on the earlier tag but was retained because the tag difference affected only the unexecuted retry branch. Overall, model choice changed reliability substantially, but the larger lesson is methodological: reporting only decisions would conceal failures in triggers, document requests and material-fact recording.
