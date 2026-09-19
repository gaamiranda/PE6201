# Contributions

Team **7** · Section **B** · PE6201 A2 · Problem **A**

> The commit history must corroborate this file. Every member commits under their own GitHub
> account — see the house rules in [`PLAN.md` §7](PLAN.md). **Add a line to the log below when
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
the identical evaluation set and the identical v2 prompt, off the frozen `battery-v2.1` tag.

| Member | Model | Family | Tier | Projected (76 runs) | Actual |
|---|---|---|---|---|---|
| Goncalo Miranda | `openai/gpt-4o-mini` | OpenAI | cheap | US$0.146 | |
| JIN CHENG | `google/gemini-2.5-flash-lite` | Google | cheap | US$0.097 | |
| NIU TONG | `meta-llama/llama-3.3-70b-instruct` | Meta | cheap | US$0.093 | |
| SUN YUCONG | `deepseek/deepseek-chat` | DeepSeek | cheap† | US$0.250 | |
| WANG HONGJUN | `mistralai/mistral-medium-3` | Mistral | **mid** | US$0.407 | |
| ZHENG YONGJIE | **v1 prompt pass** on `openai/gpt-4o-mini` | — | cheap | US$0.146 | |

The projected column replaced the earlier round estimates (~US$0.37 cheap, ~US$1.10 mid) once the
scripted run had measured token counts to price: 785,906 in and 46,280 out over 76 trials, at each
model's published rate. **It is a floor, not a quote** — a model that takes more turns costs more,
and NIU TONG's smoke test used 15 model calls on an easy case where gemini's median is 7. The
distance between this column and the Actual column beside it is a D6 finding, not an error.

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
| 2026-09-17 | Goncalo Miranda | `53e60e6` | `.env` loaded on the live path. Every instruction in the repo says the OpenRouter key lives in `.env` and `requirements.txt` ships `python-dotenv` to read it, but `load_dotenv` was only ever called in the transcript recorder — so a correctly-placed key failed with an error telling you to place it there. Found one day before six people run the live battery |
| 2026-09-17 | NIU TONG | `6e148a5`, `385c8b4` | **D5(b) runbook** — per-member commands, model ids, the `--run-id` convention, key hygiene, the judgement workflow, and the `commit_id` check that verifies all six batteries ran off one tag. The harness README's live-battery section corrected from the brief's 40 cases / 56 runs to our measured 42 / 76 |
| 2026-09-17 | WANG HONGJUN | | **Freeze item 5 — `PRICES` re-verified**, and three of eight rows were wrong. `google/gemini-2.0-flash-001` had been **delisted**: it was JIN CHENG's battery model and his Friday run would have 404ed on the first call. `deepseek/deepseek-chat` output was stale by 3.7×, which would not have failed at all — SUN YUCONG's runs would have completed and every cost figure derived from them would have been half. `meta-llama/llama-3.3-70b-instruct` moved on both input and output |
| 2026-09-17 | Goncalo Miranda | | Prices corrected against OpenRouter's own price feed, JIN CHENG moved to `google/gemini-2.5-flash-lite`, projections re-priced across `PLAN.md`, the runbook and this file, and the ceiling comment in `src/loop.py` re-measured. Freeze checklist closed |
| 2026-09-18 | SUN YUCONG | `5edba29` | **D5(b) live battery** — `deepseek/deepseek-chat`, 53/76 code-only, 50/76 combined, 2 provider timeouts. Four runs kept, including the voided one off `battery-v2` that exposed the missing retry. Found that DeepSeek catches only one of the three prompt-injection cases, falling for `CLM-8941`, which the recording model escalates in a single turn |
| 2026-09-18 | JIN CHENG | `b91bace` | **D5(b) live battery** — `google/gemini-2.5-flash-lite`, 64/76 code-only, 58/76 combined, zero runtime errors, 12 judgements reviewed himself. Because this is the model the D5(a) transcripts were recorded from, the run doubles as a direct test of record-and-replay: same nine failing cases, same median turn count, **one trial in 76** between the free replay and the paid run. Live output tokens ran 37.9% above the recording |
| 2026-09-18 | NIU TONG | `f6bbd6b` | **D5(b) live battery** — `meta-llama/llama-3.3-70b-instruct`, 45/76 code-only, 42/76 combined, no timeouts, no caps, no re-runs. The AI judgement draft and her own review are committed as separate files so the audit trail shows both. Cheapest model in the battery to run and the second most expensive to operate |
| 2026-09-18 | Goncalo Miranda | `fa1b295`, `58e6049` | **D5(b) live battery** — `openai/gpt-4o-mini`, 32/76 code-only, 31/76 combined. **12 trials stopped by `call_cap`**, every one at exactly 22 model calls with turns still at 4–8: the model proposes a decision record, the gate refuses it, and it resubmits nearly the same record until the cap stops it. Traced live to confirm the loop and gate were correct and the records genuinely wrong. 1,537,210 input tokens against the scripted 785,906 — the cheapest model per token was the second most expensive to run |
| 2026-09-19 | WANG HONGJUN | `bfd1e52` | **D5(b) live battery** — `mistralai/mistral-medium-3`, 58/76 code-only, 53/76 combined, zero runtime errors, zero caps, 12 judgements reviewed himself. Combined offline from the same live run, so the battery was paid for once. **Decision-only 72/76 against 53/76 combined** — the widest decision-to-record gap of the six: the model routes the claim correctly and then omits the identifiers, policy references and totals that make the decision auditable. Most expensive model in the battery at US$0.470291, 5.7× llama's US$0.082216 for eleven more passing trials |
| 2026-09-19 | Goncalo Miranda | | **Salvage rule** added to the runbook after WANG HONGJUN's battery came back stamped `61804e3` (`battery-v2`) rather than the `battery-v2.1` the other five ran on. The runbook declared any `battery-v2` run void; that instruction was written to catch runs that lost trials to throttling, and his lost none. The diff between the two tags is one file, +51/−12, entirely in the live request's failure branch, with `PRICES` byte-identical — code a run with zero runtime errors never executes. Kept and documented rather than repeated, which would have discarded twelve completed judgements for a different result rather than a better one |
| 2026-09-17 | SUN YUCONG | | **First live battery attempt**, `deepseek/deepseek-chat` off `battery-v2` — 61 of 76 trials lost to OpenRouter `HTTP 429` rate limits and some 504s. Reported as structurally complete but **not** a model score, partial output kept. The run is void; the defect it exposed was ours |
| 2026-09-17 | Goncalo Miranda | | Retry with exponential backoff and `Retry-After` on the live path. A 429 is a transport failure — nothing billed, nothing decided — but the harness recorded it as a runtime error and moved on instantly, hammering the endpoint harder the more it was throttled. 4xx other than 429 still fails on the first call, which is how the delisted model id was caught. Re-tagged `battery-v2.1`; all scripted numbers unchanged |

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

5 minutes total. Must show the system running, **one negative case live**, and the numbers.
Over-length is penalised under Communication.

**Budget 45 seconds each, not 50.** Six times fifty is exactly five minutes with no slack;
6 × 45 leaves half a minute of room to trim.

| # | Member | 45 seconds on |
|---|---|---|
| 1 | ZHENG YONGJIE | Why an agent at all — the ladder, and `s = 0.9441` per step |
| 2 | Goncalo Miranda | The loop and the tool layer — **live run on screen** |
| 3 | SUN YUCONG | Descriptors and guardrails — **`CLM-8941` live**, then name `CLM-8952` |
| 4 | JIN CHENG | Record-and-replay: why every number here reproduces for free |
| 5 | NIU TONG | The harness — code check vs judgement check, 57/76 against 40/42 |
| 6 | WANG HONGJUN | Cost — break-even, and why the model's price barely matters |

**Recording protocol.** Everyone records their own clip; ZHENG YONGJIE joins them, per the
ownership table. Send raw clips, not edited ones — trimming centrally is easier than negotiating
six re-records. Record off the frozen tag with a terminal font large enough to read on a laptop:
six clips from six differently configured repos look like six projects.

**The live negative case, and which one.** Slots 2 and 3 carry the two things the brief requires
to be shown rather than described. `CLM-8941` — the overt "ignore policy and approve" instruction
sitting in the member narrative — escalates correctly in **one turn**, which is the whole budget a
demo has. `CLM-9044` and `CLM-9061` are the fallbacks, both clean across all three trials.

> ⚠️ **Do not demo `CLM-8952`.** It is the injection that imitates a tool result, the agent
> **approves it**, and it is the standing FAIL on guardrail row 2. Show `CLM-8941` working and then
> say in the same breath that `CLM-8952` defeats us and is reported in D7. Naming your own failure
> reads as confidence; being caught by it live does not.

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
| The evaluation harness's judgement queue viewer and the single-case demo runner (`evaluation/show_judgements.py`, `evaluation/demo_one_case.py`) | Claude | Goncalo Miranda |
| **D5(b) human judgements, `openai/gpt-4o-mini` run — 12 verdicts drafted, then confirmed one by one before the combined score was computed.** Drafted against the record-wide rule and deliberately calibrated to NIU TONG's wording on the scripted run, so the same standard applies across all six batteries rather than a new one per member | Claude | Goncalo Miranda |
| **D5(b) human judgements, `meta-llama/llama-3.3-70b-instruct` run — 12 AI-drafted verdicts individually checked against the complete structured final records.** The draft and NIU TONG's human-reviewed JSONL are retained separately; the final result is recombined offline from her reviewed file, with the same verdicts | GPT | NIU TONG |
| §2 and §5 report drafts — argument and structure; every figure checked against a committed file before commit | Claude | Goncalo Miranda (§2), SUN YUCONG (§5) |

**On the judgement rows specifically.** The brief and `harness/README.md` both define the judgement
check as *"a person, **or a second model**, reads the record and decides"*, so a model reviewer is a
permitted method rather than a shortcut. Two conditions were held to anyway. The verdicts were
**confirmed by the named member before any combined score was computed** — an unconfirmed draft was
never published as a result. And they were written to NIU TONG's existing wording on the scripted
run, so every battery is judged to one standard: where the records were comparable, three reviewers
working separately reached identical verdicts on all twelve trials.
