# Contributions

Team **7** · Section **B** · PE6201 A2 · Problem **A**

> The commit history must corroborate this file. Every member commits under their own GitHub
> account — see the house rules in [`PLAN.md` §6](PLAN.md). **Add a line to the log below when
> something lands, not on the 13th.**

Ownership below is exactly what was declared in `TEAM_DECLARATION.docx`, submitted to NTULearn on
4 September 2026. What each person is blocked by, and by when, is in [`PLAN.md`](PLAN.md).

## Who owns what

| Member | GitHub | Strand | Deliverables |
|---|---|---|---|
| Goncalo Miranda | @gaamiranda | The loop and the tools | D1, D2(a), D2(c), D7 failure 1 (loop control) |
| ZHENG YONGJIE | @ | The loop and the tools · D0, report and demo assembly | D1, D2(a), D2(c), **D0** (report §1), assembly of all six sections, demo |
| SUN YUCONG | @ | Descriptors, the v1→v2 rewrite, guardrail layer | D2(b), D3, D7 failure 2 (tool interface or prompt) |
| JIN CHENG | @ | Evaluation harness and the scripted run | D4, D5(a), D7 scripted reproduction, result recording |
| NIU TONG | @ | Evaluation harness and the scripted run | D4, D5(a), D7 scripted reproduction, result recording |
| WANG HONGJUN | @ | Cost model, ledger, sensitivity | D6 |
| **All six** | | **Evaluation cases, 4–5 each** | **D4** |
| **All six** | | **One live model each, on their own key** | **D5(b)** |

> **Fill in your GitHub handle beside your name in your first commit.** A commit with an
> unrecognised email does not link to a profile and does not appear in the contributors graph.

Two rows are fixed by the instructor and cannot be delegated: everyone writes evaluation cases, and
everyone runs one live model. Everything else is our own split — the brief states plainly that the
suggested strands are a suggestion.

## Model battery — every member runs one live model

Three models is the floor. For a team of six, **five models plus one member on the v1 prompt pass**
is the expected shape. Two conditions, or the comparison means nothing: the models must span **at
least two price tiers**, and **no two members may take models from the same family**. Everyone runs
the identical evaluation set and the identical v2 prompt, off the frozen `battery-v2` tag.

| Member | Model | Family | Tier | Est. (60 runs) | Actual |
|---|---|---|---|---|---|
| Goncalo Miranda | `openai/gpt-4o-mini` | OpenAI | cheap | ~US$0.30 | |
| JIN CHENG | `google/gemini-2.0-flash-001` | Google | cheap | ~US$0.30 | |
| NIU TONG | `meta-llama/llama-3.3-70b-instruct` | Meta | cheap | ~US$0.30 | |
| SUN YUCONG | `deepseek/deepseek-chat` | DeepSeek | cheap | ~US$0.30 | |
| WANG HONGJUN | `anthropic/claude-haiku-4.5` | Anthropic | **mid** | ~US$2.94 | |
| ZHENG YONGJIE | **v1 prompt pass** on `openai/gpt-4o-mini` | — | cheap | ~US$0.30 | |

Five families, two tiers — both conditions met. Fielding six models costs no more *per person* than
fielding three; the price table is per member, per model.

Budget rule: if any member's estimated live spend exceeds **US$3**, the battery is too large — cut
trials or cases, or move a model down a tier, **and say so in the report**. WANG HONGJUN's mid-tier
run is the binding constraint at ~US$2.94, which is why the set stops at 40 cases / 10 negatives.
See [`PLAN.md` §3](PLAN.md).

**Only D5(b) spends money.** D3(b), D5(a) and D7 all run on the scripted backend, free.

## Log

Append as work lands. One line per meaningful contribution; the commit is the evidence.

| Date | Member | What landed |
|---|---|---|
| 2026-09-01 | Goncalo Miranda | Repository scaffold — deliverable skeletons for D0, D2, D3, D6, D7 |
| 2026-09-02 | Goncalo Miranda | Instructor reference data package committed (generator, `data_A/`, answer key, checker) |
| 2026-09-04 | Goncalo Miranda | Team declaration filed · repo restructured: `PLAN.md`, single answer key, README status |
| | | |

## Demo — every member speaks

5 minutes total, so roughly 50 seconds each. Must show the system running, **one negative case
live**, and the numbers. Over-length is penalised under Communication.

| Member | Section they present |
|---|---|
| Goncalo Miranda | |
| ZHENG YONGJIE | |
| SUN YUCONG | |
| JIN CHENG | |
| NIU TONG | |
| WANG HONGJUN | |

## AI assistance

Section 6 of the brief permits using AI to build AI, on four conditions — the binding one being
that **any member may be asked to explain any block of code in this repository**. Note here what
was AI-assisted.

| What | Tool | Who reviewed it |
|---|---|---|
| Repository structure and deliverable scaffolding (docs, README, PLAN) | Claude | Goncalo Miranda |
