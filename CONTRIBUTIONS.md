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
| ZHENG YONGJIE | @riv7128-lgtm | The loop and the tools · D0, report and demo assembly | D1, D2(a), D2(c), **D0** (report §1), assembly of all six sections, demo |
| SUN YUCONG | @cherrysun11111-debug | Descriptors, the v1→v2 rewrite, guardrail layer | D2(b), D3, D7 failure 2 (tool interface or prompt) |
| JIN CHENG | @cccheng1100 | Evaluation harness and the scripted run | D4, D5(a), D7 scripted reproduction, result recording |
| NIU TONG | @Tong16-lab | Evaluation harness and the scripted run | D4, D5(a), D7 scripted reproduction, result recording |
| WANG HONGJUN | @hongjun002 | Cost model, ledger, sensitivity | D6 |
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

| Member | Model | Family | Tier | Est. (76 runs) | Actual |
|---|---|---|---|---|---|
| Goncalo Miranda | `openai/gpt-4o-mini` | OpenAI | cheap | ~US$0.37 | |
| JIN CHENG | `google/gemini-2.0-flash-001` | Google | cheap | ~US$0.37 | |
| NIU TONG | `meta-llama/llama-3.3-70b-instruct` | Meta | cheap | ~US$0.37 | |
| SUN YUCONG | `deepseek/deepseek-chat` | DeepSeek | cheap | ~US$0.37 | |
| WANG HONGJUN | `mistralai/mistral-medium-3` | Anthropic | **mid** | ~US$3.75 | |
| ZHENG YONGJIE | **v1 prompt pass** on `openai/gpt-4o-mini` | — | cheap | ~US$0.37 | |

Five families, two tiers — both conditions met. Fielding six models costs no more *per person* than
fielding three; the price table is per member, per model.

Budget rule: if any member's estimated live spend exceeds **US$3**, the battery is too large — cut
trials or cases, or move a model down a tier, **and say so in the report**.

> ⚠ **OPEN DECISION — owner JIN CHENG (D4), due before the 10 Sep freeze.** The set closed at
> **42 cases with 17 negatives**, not the 40/10 planned in [`PLAN.md` §3](PLAN.md). At one trial
> per ordinary case and three per negative that is **25 + 51 = 76 runs per model**, which puts
> WANG HONGJUN's mid-tier battery at roughly **US$3.75 — over the US$3 rule**. Two ways out, and
> it has to be a decision rather than an accident: trim the negative count, or move WANG HONGJUN
> to the cheap tier and state that in the report. The brief permits the second explicitly.

**Only D5(b) spends money.** D3(b), D5(a) and D7 all run on the scripted backend, free.

## Log

Append as work lands. One line per meaningful contribution; the commit is the evidence.

| Date | Member | Commit | What landed |
|---|---|---|---|
| 2026-09-01 | Goncalo Miranda | `a12156f` | Repository scaffold — deliverable skeletons for D0, D2, D3, D6, D7 |
| 2026-09-01 | Goncalo Miranda | `ce01322`, `51daad6` | Team declaration |
| 2026-09-04 | Goncalo Miranda | `4fb6d33` | Instructor reference data package (generator, `data_A/`, `data_B/`, answer keys, checker) |
| 2026-09-04 | Goncalo Miranda | `5f064e9` | Repo restructured: `PLAN.md`, single answer key, `src/contracts.py` — the frozen types four people were blocked on |
| 2026-09-06 | ZHENG YONGJIE | `04882a5` | **D0** — the ladder, both Capsule 1 tests, the five statements of what good looks like |
| 2026-09-06 | Goncalo Miranda | `976ed2d` | **The agent** — tool layer, ReAct loop with multi-call turns, vendor seam, ground-truth benchmark (D1, D2a) |
| 2026-09-06 | Goncalo Miranda | `b0464fa` | Evaluation cases `CLM-9001`–`9005` — boundary and near-miss cases (5) |
| 2026-09-07 | ZHENG YONGJIE | `e0ca263`, `c7c5096` | Evaluation cases `CLM-9101`–`9105` — policy/pre-auth start boundaries, per-policy exclusions (5) |
| 2026-09-07 | Goncalo Miranda | `67923de` | GitHub handles recorded against each member, so the history is attributable |
| 2026-09-07 | JIN CHENG | `8f900ea`, `6f31442` | Evaluation cases `CLM-9031`–`9035` — document gap behind a valid pre-auth, benign narrative control (5) |
| 2026-09-07 | SUN YUCONG | `1ed4c77`, `f9c9676` | Evaluation cases `CLM-9061`–`9065` — lapsed-inside-dates, pre-auth not yet valid, limit exceeded by one, valid pre-auth on an excluded line (5) |
| 2026-09-07 | NIU TONG | `6423572`, `4f82d0e` | Evaluation cases `CLM-9041`, `9042`, `9044`, `9046`, `9047` — pre-auth last valid day, injection on a clean claim, duplicate with reordered lines against a prior decline (5) |
| 2026-09-07 | WANG HONGJUN | `f7ca294`, `9a87705` | Evaluation cases `CLM-9081`–`9082` — false-positive controls for the guardrail layer: a benign bracketed narrative and a clinical use of "ignore" (2) |

**Evaluation set closed at 42 cases** — 15 shipped by the instructor plus 27 written by the team.
Every case was labelled from the Appendix A routing table before any agent run, and every label was
checked against the tool layer before it was committed. `check_my_data.py` passes.

| Member | Cases written | Ids |
|---|---|---|
| Goncalo Miranda | 5 | `CLM-9001`–`9005` |
| ZHENG YONGJIE | 5 | `CLM-9101`–`9105` |
| JIN CHENG | 5 | `CLM-9031`–`9035` |
| SUN YUCONG | 5 | `CLM-9061`–`9065` |
| NIU TONG | 5 | `CLM-9041`, `9042`, `9044`, `9046`, `9047` |
| WANG HONGJUN | 2 | `CLM-9081`–`9082` |

Cases were screened before encoding: five were rejected for duplicating coverage already in the set
(one of them also ambiguous — it matched two routing rows, so no answer key could grade it). A
rejected case is recorded here because the screening is part of D4, not a gap in anyone's
contribution.

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
| Agent loop, tool layer, vendor seam and ground-truth benchmark (`src/`) | Claude | Goncalo Miranda |
| D0 long-form draft — argument and structure; every figure in it re-measured before commit | Claude | ZHENG YONGJIE, Goncalo Miranda |
| Encoding team members' cases into the fixtures, and checking each label against the routing table | Claude | Each case's author |
