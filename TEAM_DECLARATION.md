# PE6201 A2 — Team Declaration (working copy)

> **Changed 1 September 2026.** The instructor now ships an official **`TEAM_DECLARATION.docx`**
> template on NTULearn, and the change notice says: *"Use it as it is; do not redesign it."*
> **Download it and type these answers into it.** This file is now our agreed working copy, not the
> thing we submit.
>
> The form also asks for a **signature and date**, and prints the A2 timeline.

**Due Friday 4 September 2026, 23:59 SGT**, into the team's A2 submission folder on NTULearn.
A team that files nothing has an incomplete submission.

---

## 1 · Team ID and section

**Team:** 7
**Section:** B

## 2 · Members

> **Matriculation numbers are deliberately not in this file.** This repository becomes public
> before submission, and matriculation numbers are personal data for six people. They live only in
> `TEAM_DECLARATION.docx`, which is gitignored and goes to NTULearn.

| # | Name |
|---|---|
| 1 | Goncalo Miranda |
| 2 | JIN CHENG |
| 3 | NIU TONG |
| 4 | SUN YUCONG |
| 5 | WANG HONGJUN |
| 6 | ZHENG YONGJIE |

## 3 · Problem chosen

**[x] Problem A — Health-insurance claim first response**
**[ ] Problem B — Outpatient referral coordination**

## 4 · Who owns what

> The listed strands are **a suggestion we are free to replace** (change notice, 1 Sep). Two rows
> are **not optional**: everyone writes evaluation cases, and **everyone runs one live model —
> name the model beside each person.**

| Member | Strand | Deliverables | Live model they run (D5b) | Tier |
|---|---|---|---|---|
| Goncalo Miranda | The loop and the tools | D1, D2(a), D2(c), **D7 failure 1** (loop control) | `openai/gpt-4o-mini` | cheap |
| ZHENG YONGJIE | The loop and the tools · **D0, report and demo assembly** | D2(a), **D0** (report §1), assembly of all six sections, demo | **v1 prompt pass** on `openai/gpt-4o-mini` | cheap |
| SUN YUCONG | Descriptors, v1→v2 rewrite, guardrail layer | D2(b), D3, **D7 failure 2** (tool interface or prompt) | `deepseek/deepseek-chat` | cheap |
| JIN CHENG | Evaluation harness and the scripted run | D4, D5(a), **D7 scripted reproduction** | `google/gemini-2.0-flash-001` | cheap |
| NIU TONG | Evaluation harness and the scripted run | D4, D5(a), **D7 scripted reproduction** | `meta-llama/llama-3.3-70b-instruct` | cheap |
| WANG HONGJUN | Cost model, ledger, sensitivity | D6 | `anthropic/claude-haiku-4.5` | **mid** |
| **All members** | **Evaluation cases, 5–8 each** | **D4** | — | — |

Five families (OpenAI · Google · Meta · DeepSeek · Anthropic), two price tiers — both battery
conditions satisfied. Estimated team spend under **US$4.50** total.

> **Verify every model id and its price on openrouter.ai/models before Friday.** Ids and prices
> change; a wrong id is a runtime 404. Avoid `:free` variants (rate-limited, and they leave D6 with
> no price to divide by) and reasoning models (hidden thinking tokens bill as output at 4–5×).

> **The instructor's strand table names neither D0 nor D7.** Its Feeds column runs D1, D2(a),
> D2(c), D2(b), D3, D4, D5(a), D6, D5(b) and "report sections 4 and 5" — D0 and D7 appear nowhere.
> We have named both, which the change notice permits ("the listed strands are a suggestion you are
> free to replace with your own").

**Still to settle before Friday:**

1. ~~Nobody owns D0 and the report.~~ **ZHENG YONGJIE has it** — the lightest-loaded member, and the
   only battery job he carries is the v1 pass. This keeps the sole coder off the two most
   deadline-exposed writing tasks.
2. ~~Five model names plus one v1 pass.~~ **Done** — see the table above. Confirm the ids on
   openrouter.ai/models before Friday.
3. **D7 is split five ways, and failure 2 is constrained.** Failure 1 (loop control) is the loop
   owner's. Failure 2 **must sit in the tool interface or the prompt** — not loop control again, and
   not a guardrail, because guardrails are the code layer. Cheapest route: make failure 2 the
   **v1 descriptor** SUN YUCONG already builds for D2(b) — revert one tool to its fat, unbounded
   return, show the confident wrong answer, fix it at the interface. One piece of work, two
   deliverables. The harness owners script both reproductions; the two failure owners co-write
   report §5 and one of them demos a failure live.

4. **The report is drafted per section, assembled by one.** Each strand owner drafts their own
   section — they have the numbers — and ZHENG YONGJIE edits to 2,000 words and keeps one voice.
   A single person writing all six sections from scratch in the last 48 hours is how teams overrun.

## 5 · Repository URL

https://github.com/gaamiranda/PE6201

## 6 · Contribution statement

> This section is **not optional**. State one of two things — do not leave it blank.
> Silence at the checkpoint is read as "all members are contributing", and a team that raises a
> problem on 13 September instead has no warning, no remediation window and no contemporaneous
> record. Naming a problem here is not an accusation; it starts a conversation with a deadline
> attached, and the member gets nine days to remediate.

**All members are contributing.**

<!-- OR, if that is not true, delete the line above and state instead:
     - the member's name
     - what was agreed
     - what has actually happened
-->
