# Contributions

Team **7** · Section **B** · PE6201 A2 · Problem **A**

> The commit history must corroborate this file. Every member commits under their own GitHub
> account — see the house rules in [`PLAN.md` §6](PLAN.md). **Add a line to the log below when
> something lands, not on the 20th.**

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
| WANG HONGJUN | `mistralai/mistral-medium-3` | Mistral | **mid** | ~US$1.10 | |
| ZHENG YONGJIE | **v1 prompt pass** on `openai/gpt-4o-mini` | — | cheap | ~US$0.37 | |

Five families, two tiers — both conditions met. Fielding six models costs no more *per person* than
fielding three; the price table is per member, per model.

Budget rule: if any member's estimated live spend exceeds **US$3**, the battery is too large — cut
trials or cases, or move a model down a tier, **and say so in the report**.

> ✅ **DECIDED, 8 Sep — and it goes in the report.** The set closed at **42 cases with 17
> negatives**, not the 40/8 the brief prices. At one trial per ordinary case and three per
> negative that is **25 + 51 = 76 runs per model**, against the brief's 56. On `claude-haiku-4.5`
> that put WANG HONGJUN at roughly **US$3.75 — over our own US$3 rule**.
>
> We kept all 17 negatives and **changed the model instead**: WANG HONGJUN moves from
> `anthropic/claude-haiku-4.5` to `mistralai/mistral-medium-3`, about **US$1.10** for the same
> 76 runs. Two reasons. Negatives are where the brief says models diverge most, so cutting them
> would remove the finding we are looking for. And dropping WANG HONGJUN to the *cheap* tier —
> the obvious alternative — would leave all six of us on one tier and fail the brief's own
> condition that the set span at least two price tiers.
>
> **Consequence to state with every pass rate: 76 runs, not 56.** The brief allows going above
> its numbers and requires the trial count beside the figure.

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
| 2026-09-09 | JIN CHENG | `8ff0287`, `5270262`, `570d6c6`, `9b82b5f` | **D5(a)** — record-and-replay: `record_transcripts.py`, the 42-case transcript, `check_scripted_replay.py`, and deletion of the throwaway `dev_transcripts.py` |
| 2026-09-09 | Goncalo Miranda | `5e68bda`, `c187b2a`, `f2387d7` | Recording made opt-in (unconditional recording would corrupt the transcript on every battery run); `Final:` accepts Python literals as `Action:` already did; every battery model priced; caps set from the measured distribution |
| 2026-09-10 | Goncalo Miranda | `91da36f` | `prompt_version` wired through to the tool manual — v1 and v2 had been byte-identical, so the D2(b) comparison would have measured nothing |
| 2026-09-13 | NIU TONG | `afdfed8` | **D5(a)** — the evaluation harness: `run_eval.py`, 26 unit tests, code-vs-judgement grading, per-trial and summary evidence |
| 2026-09-13 | Goncalo Miranda | `b1bc7d8`, `7a87f13`, `dccda1f` | `validator_overridden` / `validator_gaps` — a record the evidence validator rejected and was overruled on is now visible instead of silent; harness grading fails such records; NIU TONG's files moved into `harness/` and `results/evaluations/` |
| 2026-09-15 | SUN YUCONG | `bb5ce16`–`1e12115` | **D2(b) + D3(a)** — the six-field descriptors, the v2 `check_coverage` return-shape rewrite, the real autonomy gate replacing the permissive stub, and the ten-case guardrail checklist |
| 2026-09-15 | Goncalo Miranda | `f283a93` | Budget ceiling re-measured across the whole battery — the single-model value aborted 34 of `mistral-medium-3`'s 42 runs; `run_guardrail_checklist.py` so the checklist's observed-result column is produced rather than predicted |
| 2026-09-15 | Goncalo Miranda | `d5ac010` | **D7 failure 1** — the working agent minus action de-duplication: the same claim written four times, invisible in every aggregate metric |
| 2026-09-15 | Goncalo Miranda | `2770118` | **D2(c)** — sequential vs parallel measured on identical calls; the dependency rule permits 17.6% fewer turns and the model captures 2.7% of it |
| 2026-09-15 | Goncalo Miranda | `4d6015e`, `7026c17` | Three prompt/parser defects found and fixed: the tool manual taught a syntax the parser rejected (12.7% of replies lost), the prompt asked for JSON while the parser demanded Python, and two of the three outcomes had no tool without saying so. All 42 transcripts re-recorded; decisions 90.5% → **95.2%**, projected cost down 25% |
| 2026-09-15 | SUN YUCONG | `07c89c7`, `c9d5088` | **D7 failure 2** — the v2 `check_coverage` shape, measured in three arms so the return shape is separated from the descriptor that shipped with it; the old shape's contradictory observation found on `CLM-9065` |
| 2026-09-15 | NIU TONG | `7d3ddaa` | **D5(a)** — the judgement rule settled and written down: a `must_record` fact counts anywhere in the structured record, not only in `reason`. Harness and queue changed to match, 2 tests added, all 12 judgements re-reviewed against the re-recorded transcripts |
| 2026-09-15 | Goncalo Miranda | | Summary paths made repo-relative — the regenerated evidence file had baked in an absolute local directory, which leaks a personal path and makes two identical runs differ byte-for-byte |
| 2026-09-16 | ZHENG YONGJIE | `53fdd49` | **D0** — the reliability arithmetic corrected to the combined pass rate, plus fourteen overclaims found by reading the document against the code and the trial records: a code check that did not exist, a poka-yoke stated as a guarantee, turn counts confused with model calls, and grading coverage overstated |
| 2026-09-16 | Goncalo Miranda | | The policy-id poka-yoke downgraded from a guarantee to a traceability property in `src/tools.py`, `src/contracts.py` and `docs/D2-tool-layer.md` — the same overclaim ZHENG YONGJIE found in D0 had propagated to six more places |

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
