# PE6201 A2 — Team Declaration (repository mirror)

> **Filed 4 September 2026.** The submitted artefact is the instructor's
> **`TEAM_DECLARATION.docx`**, checked into the team's A2 folder on NTULearn. That file is the
> authoritative one. This is a public mirror of it, **without the matriculation numbers** — this
> repository is public, and those are personal data for six people.
>
> **Ownership has not changed since it was filed.** If the team re-divides work, change
> [`PLAN.md`](PLAN.md) and [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md) — not this file, which records
> what was declared.

---

## 1 · Team, section, problem

**Team 7 · Section B · Problem A — Health-insurance claim first response**

## 2 · Members

| # | Name |
|---|---|
| 1 | Goncalo Miranda |
| 2 | JIN CHENG |
| 3 | NIU TONG |
| 4 | SUN YUCONG |
| 5 | WANG HONGJUN |
| 6 | ZHENG YONGJIE |

Matriculation numbers are in the submitted `.docx` only (gitignored).

## 3 · Repository

https://github.com/gaamiranda/PE6201

## 4 · Who owns what

| Strand | Feeds | Owner(s) |
|---|---|---|
| The loop and the tools | D1, D2(a), D2(c), D7 failure 1 (loop control) | Goncalo Miranda · ZHENG YONGJIE |
| Descriptors, the v1→v2 rewrite, guardrail layer | D2(b), D3, D7 failure 2 (tool interface or prompt) | SUN YUCONG |
| Evaluation harness and the scripted run | D4, D5(a), D7 scripted reproduction and result recording | JIN CHENG · NIU TONG |
| Cost model, ledger, sensitivity | D6 | WANG HONGJUN |
| D0, report and demo assembly | D0 (report §1), assembly of all six sections, demo | ZHENG YONGJIE — each strand owner drafts their own section |
| **Evaluation cases — everyone** | D4 | all six, 4–5 each |
| **Live model battery — everyone, one model each** | D5(b) | see below |

| Member | Live model (D5b) | Family | Tier |
|---|---|---|---|
| Goncalo Miranda | `openai/gpt-4o-mini` | OpenAI | cheap |
| JIN CHENG | `google/gemini-2.0-flash-001` | Google | cheap |
| NIU TONG | `meta-llama/llama-3.3-70b-instruct` | Meta | cheap |
| SUN YUCONG | `deepseek/deepseek-chat` | DeepSeek | cheap |
| WANG HONGJUN | `anthropic/claude-haiku-4.5` | Anthropic | **mid** |
| ZHENG YONGJIE | **v1 prompt pass** on `openai/gpt-4o-mini` | — | cheap |

Five families, two price tiers — both battery conditions satisfied.

> **This table is the declaration as submitted on 4 September and is left as submitted.** One row
> has changed since: WANG HONGJUN moved from `anthropic/claude-haiku-4.5` to
> `mistralai/mistral-medium-3` when the evaluation set closed at 76 runs rather than 56 and haiku
> came to roughly US$3.75, over our own US$3 rule. Both battery conditions still hold — five
> families, two tiers. The reasoning is in [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md) and the live
> table there is the current one. **Do not "fix" this table to match**: it records what was filed.

## 5 · Contribution statement

**All members are contributing.**
