# PLAN — who does what, who they wait on, and by when

Team **7** · Section **B** · Problem **A — health-insurance claim first response**

**This is the file to read first.** Ownership comes from `TEAM_DECLARATION.docx`, which was
submitted to NTULearn on 4 September. This file adds the two things the declaration does not have:
**what blocks you**, and **when it is due**.

- Ownership → this file and `CONTRIBUTIONS.md`
- What has actually landed → the log at the bottom of `CONTRIBUTIONS.md`
- How to write evaluation cases → `evaluation/cases/README.md`
- How to extend the data → `docs/D4-data-and-cases.md`

---

## 1 · The six jobs

| Member | Owns | Deliverables |
|---|---|---|
| **Goncalo Miranda** | The loop and the tools | D1, D2(a), D2(c), D7 failure 1 (loop control) |
| **ZHENG YONGJIE** | The loop and the tools · D0, report and demo assembly | D1, D2(a), D2(c), **D0**, report §1, assembly of all six sections, demo |
| **SUN YUCONG** | Descriptors, the v1→v2 rewrite, guardrail layer | D2(b), D3, D7 failure 2 (tool interface or prompt) |
| **JIN CHENG** | Evaluation harness and the scripted run | D4, D5(a), D7 scripted reproduction, result recording |
| **NIU TONG** | Evaluation harness and the scripted run | D4, D5(a), D7 scripted reproduction, result recording |
| **WANG HONGJUN** | Cost model, ledger, sensitivity | D6 |
| **All six** | Evaluation cases (see §3) · one live model each (see §4) | D4, D5(b) |

---

## 2 · Who waits on whom

The only hard dependency in the build is **the shape of a run result**. Everything else can start now.

```
  Goncalo + ZHENG YONGJIE
  src/contracts.py  ─────────┬──────► JIN CHENG + NIU TONG   (harness reads the record)
  (the decision-record       │
   shape + tool signatures)  ├──────► SUN YUCONG             (descriptors need signatures)
                             │
                             └──────► WANG HONGJUN           (D6 needs turns/tokens/cost fields)

  JIN CHENG + NIU TONG
  working harness ───────────┬──────► SUN YUCONG             (D2(b) v1 vs v2 needs a runner)
                             ├──────► WANG HONGJUN           (D6 needs a measured pass rate)
                             └──────► everyone               (D5(b) battery)

  All six
  evaluation cases ─────────────────► JIN CHENG + NIU TONG   (nothing to run without them)
```

**Per person:**

| Member | Start now, blocked by nobody | Blocked by | Blocks |
|---|---|---|---|
| Goncalo | `src/contracts.py`, the tool set table in D2(a), the loop | — | everyone |
| ZHENG YONGJIE | **D0 §(c) — the five statements, today**, then the tool set with Goncalo | — | nothing early; report assembly at the end |
| SUN YUCONG | The six-field descriptor template, the guardrail case list | tool signatures (Goncalo), then the harness | D2(b) numbers for the cost ledger |
| JIN CHENG | The scripted backend, the case loader | `src/contracts.py` | the battery, D6, D7 |
| NIU TONG | Instrumentation (turns, tokens, cost, caps fired, tools in order) | `src/contracts.py` | the battery, D6, D7 |
| WANG HONGJUN | The Class 5 notebook, the three-layer skeleton, the price table | measured pass rate + token counts | report §4 |

**Nobody has to wait to write evaluation cases.** That work needs no code and it is 40% of the
evidence the submission rests on.

---

## 3 · Evaluation cases — the baton

We are at **15 shipped cases**. Target is **40**, so **25 more**, roughly **4–5 each**.

**We write them one at a time, in this order.** No branches, no merge conflicts. When you finish,
push and tell the next person.

| # | Member | Claim ids | Members | Policies | Pre-auth | Prior decisions | New procedure codes |
|---|---|---|---|---|---|---|---|
| 1 | Goncalo Miranda | `CLM-9001`–`9020` | `M-7001`–`7010` | `POL-8001`–`8010` | `PA-9001`–`9010` | `CLM-9501`–`9510` | `91001`–`91010` |
| 2 | JIN CHENG | `CLM-9021`–`9040` | `M-7011`–`7020` | `POL-8011`–`8020` | `PA-9011`–`9020` | `CLM-9511`–`9520` | `92001`–`92010` |
| 3 | NIU TONG | `CLM-9041`–`9060` | `M-7021`–`7030` | `POL-8021`–`8030` | `PA-9021`–`9030` | `CLM-9521`–`9530` | `93001`–`93010` |
| 4 | SUN YUCONG | `CLM-9061`–`9080` | `M-7031`–`7040` | `POL-8031`–`8040` | `PA-9031`–`9040` | `CLM-9531`–`9540` | `94001`–`94010` |
| 5 | WANG HONGJUN | `CLM-9081`–`9100` | `M-7041`–`7050` | `POL-8041`–`8050` | `PA-9041`–`9050` | `CLM-9541`–`9550` | `95001`–`95010` |
| 6 | ZHENG YONGJIE | `CLM-9101`–`9120` | `M-7051`–`7060` | `POL-8051`–`8060` | `PA-9051`–`9060` | `CLM-9551`–`9560` | `96001`–`96010` |

Stay inside your block and two people can never collide, even if the baton slips.

**Your turn, in five steps** — the full instructions are in
[`evaluation/cases/README.md`](evaluation/cases/README.md):

```bash
git pull                                   # 1 · always, before you type anything
# 2 · add your rows to the EXTRA_* lists at the bottom of A2_reference_data/make_fixtures_A.py
# 3 · add one label per case to A2_reference_data/expected_outcomes_A.json  — BY HAND
cd A2_reference_data
python3 make_fixtures_A.py                 # 4 · regenerate data_A/
python3 check_my_data.py                   # 5 · must say "Your data hangs together."
git add -A && git commit -m "eval cases: <your name>, CLM-90xx..90yy" && git push
# then tell the next person on the list
```

**Do not push if `check_my_data.py` fails.** It fails for the whole team, not just you.

### How many negatives

The 15 shipped cases already include **9 negatives** (6 escalate, 3 request_document). A 40-case
set should carry 6–10. We will land around **10**, which is fine — but note the run arithmetic,
because it sets the budget:

| Set | Ordinary × 1 trial | Negative × 3 trials | Runs per model | Cheap tier | Mid tier |
|---|---|---|---|---|---|
| 40 cases, 8 negative | 32 | 24 | **56** | US$0.27 | US$2.76 |
| 40 cases, 10 negative | 30 | 30 | **60** | US$0.30 | US$2.94 |
| 45 cases, 12 negative | 33 | 36 | **69** | US$0.35 | **US$3.38 — over budget** |

**The mid-tier battery is the constraint.** The brief's rule is US$3 per member. So: **stop the set
at 40 cases and 10 negatives.** If we want more, WANG HONGJUN moves to a cheaper model and we say
so in the report — the brief explicitly allows that, but it has to be a decision, not an accident.

---

## 4 · The live battery — everyone runs one

From `TEAM_DECLARATION.docx`, with **one change since**: WANG HONGJUN moved off
`anthropic/claude-haiku-4.5`, which came to roughly US$3.75 over our 76-trial schedule and broke
our own US$3 rule. The reasoning is recorded in [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md).

| Member | Model | Family | Tier | Projected, 76 trials |
|---|---|---|---|---|
| Goncalo Miranda | `openai/gpt-4o-mini` | OpenAI | cheap | US$0.146 |
| JIN CHENG | `google/gemini-2.0-flash-001` | Google | cheap | US$0.097 |
| NIU TONG | `meta-llama/llama-3.3-70b-instruct` | Meta | cheap | US$0.108 |
| SUN YUCONG | `deepseek/deepseek-chat` | DeepSeek | cheap | US$0.123 |
| WANG HONGJUN | `mistralai/mistral-medium-3` | Mistral | **mid** | US$0.407 |
| ZHENG YONGJIE | ✅ **v1 prompt pass** on `openai/gpt-4o-mini` | — | cheap | US$0.146 |

Five families, two price tiers — both conditions met. Own key, own model, own numbers.

> **These are projections, not quotes.** They take the scripted run's measured token counts
> (785,906 in / 46,280 out over 76 trials) and price them at each model's published rate. A live
> run that takes more turns costs more: NIU TONG's smoke test used **15 model calls on an easy
> case where gemini's median is 7**. Treat these as a floor and expect chattier models to exceed
> them. The gap between projection and bill is WANG HONGJUN's to report in D6.

> ✅ **The v1 pass is ZHENG YONGJIE's, decided and unchanged across all four files.** He runs
> `--prompt-version v1` on `openai/gpt-4o-mini` — the same model Goncalo runs v2 on, because to
> compare prompts you hold the model fixed. It is the **only** measurement in this project that
> can show whether the six-field descriptor makes the model better rather than merely bigger:
> scripted replay is keyed on `(case_id, turn)` alone, so it returns identical replies under both
> prompts and can price the rewrite but never grade it. We know v2 costs **+275 tokens on every
> model call**; without this run, `docs/D2-tool-layer.md` reports that cost with nothing beside it.
>
> ```bash
> python3 harness/run_eval.py --backend openrouter \
>   --model openai/gpt-4o-mini --prompt-version v1
> ```

**Three rules, or the comparison is void:**

1. Everyone runs the **same commit** — the `battery-v2` tag (see §5).
2. Everyone runs the **same v2 prompt**. The model id is the only string that differs.
3. **Verify your model id on openrouter.ai/models before you run.** A wrong id is a runtime 404.
   Avoid `:free` variants and reasoning models.

**Only this spends money.** D3(b), D5(a) and D7 all run on the scripted backend, free.
Debug scripted. If you are burning live tokens to find a bug, stop.

---

## 5 · Dates

Boilerplate — adjust in this file if the team agrees something else.

> **The deadline moved to Sunday 20 September.** The dates below were rewritten on 16 Sep to
> match. Everything above the rule is what actually happened, dated when it landed; everything
> below it is what is left.

| Date | What | Who |
|---|---|---|
| Fri 4 Sep | ✅ Declaration filed · repo restructured · `src/contracts.py` frozen | Goncalo, ZHENG YONGJIE |
| Sat 6 Sep | ✅ **D0** · the agent: tool layer, ReAct loop, vendor seam (D1, D2a) | ZHENG YONGJIE, Goncalo |
| Sun 7 Sep | ✅ Case baton finished — 42 cases labelled, `check_my_data.py` clean | all six |
| Tue 9 Sep | ✅ **D5(a)** record-and-replay: recorder, 42-case transcript, replay check | JIN CHENG |
| Sat 13 Sep | ✅ **D5(a)** the evaluation harness, 26 tests, code-vs-judgement grading | NIU TONG |
| Mon 15 Sep | ✅ **D2(b) + D3** descriptors, v2 shape, autonomy gate, guardrail checklist | SUN YUCONG |
| Mon 15 Sep | ✅ **D7** both failures · **D2(c)** · three prompt/parser defects fixed, all 42 re-recorded | Goncalo, SUN YUCONG |
| Mon 15 Sep | ✅ Judgement rule settled record-wide · all 12 judgements re-reviewed | NIU TONG |
| ————— | **— everything below is what is left —** | |
| **Wed 16 Sep** | **D6** drafted on the scripted numbers · `PRICES` re-verified · freeze checklist closed | WANG HONGJUN |
| **Thu 17 Sep 23:59** | 🔒 **FREEZE.** Tag `battery-v2`. Eval set, v2 prompt and harness final. | Goncalo tags |
| **Fri 18 Sep** | **Everyone runs their live battery** off that tag, commits their numbers | all six |
| **Sat 19 Sep** | D6 actuals filled · result tables · six report sections assembled · demo recorded · self-appraisal | WANG HONGJUN, ZHENG YONGJIE, all six |
| **Sun 20 Sep** | Final read-through · **submit by 23:59 SGT** | all six |
| Wed 23 Sep | Peer rating — participation requirement | all six |

**Thursday's freeze is the one date that cannot slip.** Six people running the battery off six
different commits silently voids the whole comparison. The extra week bought slack everywhere
except here: the battery still needs a day of its own, and the assembly still needs the battery.

### The freeze checklist — 17 Sep

Things that are legitimately unanswerable today and become answerable the moment D4 and D5(a)
land. Each has a named owner and a document it has to be written back into — a deferred number is
a tracked dependency, not a free pass.

| # | What closes | Unblocked by | Written back into | Owner |
|---|---|---|---|---|
| 1 | ✅ **D0(b) reliability arithmetic** — `P = 0.7500` (57/76 combined), `T = 5`, `s = 0.9441`, with all three harness rates named so they cannot be confused again. Fourteen further overclaims found and corrected in review | D4 labels + the D5(a) run | `docs/D0-why-an-agent.md` and the D0 submission draft | ZHENG YONGJIE |
| 1b | ✅ **D0(a) turn counts** — predicted turns replaced with measured: `CLM-8910` 2 turns / 2 tools / 3 calls, `CLM-8842` 9 turns / 8 tools / 11 calls, each shown beside what the dependency rule permits | the D5(a) run | the D0 submission draft | ZHENG YONGJIE |
| 2 | ✅ **`Guards.step_cap` and `budget_ceiling_usd`** — 12 turns, 22 model calls, US$0.016, every one from the measured distribution and the ceiling measured across the whole battery | the D5(a) run | `src/loop.py` | SUN YUCONG |
| 3 | ✅ **D2(b) v1 → v2** — manual 265 → 540 tokens, and what that costs over a full schedule | a working harness | `docs/D2-tool-layer.md` | SUN YUCONG |
| 4 | ✅ **D2(c) sequential vs parallel** — measured on identical recorded calls, three arms | D5(a) replay over the whole set | `docs/D2-tool-layer.md` | Goncalo, ZHENG YONGJIE |
| 5 | ⬜ **`PRICES` re-verified** on openrouter.ai **before anyone spends** | — do it before the freeze | `src/backends.py` | WANG HONGJUN |

**Five of the six are closed. One is open.**

**Item 5 — WANG HONGJUN, and it blocks spending.** `price()` raises on an *unknown* model id but
will happily compute with a stale rate, so a wrong number there corrupts D6 silently rather than
loudly. Nothing else in the repository will catch it.

**Item 1 closed, and it is worth recording how.** `docs/D0-why-an-agent.md` had quoted
`P = 0.8289 (63/76 combined)`; 63/76 is the harness's **code-only** rate and the combined rate is
**57/76 = 0.75**, which moved `s` to 0.9441 and the whole `T` table with it. Reviewing that fix,
ZHENG YONGJIE checked the document line by line against the code and the trial records and found
**fourteen** further statements that overclaimed — among them a "code-checked on every evaluation
run" that named a check the harness has never performed, and a poka-yoke described as a guarantee
that had propagated into four files including `src/contracts.py`. All corrected. The lesson is
cheap to state and was expensive to find: **a document drifts from the code silently, because
nothing fails when it does.**

---

## 6 · House rules

- **Commit under your own account.** Individual marks are adjusted against the commit history,
  and section 8 says the log must be corroborated by it. Once, before your first commit:
  ```bash
  git config user.name "Your Name"
  git config user.email "the-email-on-your-github-account"
  ```
- **Add a line to `CONTRIBUTIONS.md` when something lands.** Not on the 20th.
- **Never commit a key.** `.env` is gitignored; keep it that way.
- **Never edit or delete a row the instructor shipped.** New ids only, inside your block.
  `check_my_data.py` fingerprints every shipped row and will name the one that moved.
- **No framework owning the loop** (LangChain, LangGraph, CrewAI, AutoGen). Ordinary libraries for
  everything else are fine.
- **`BACKEND = "scripted"` stays the default.** If the harness does not run that way,
  Technical Execution is capped.
- **You must be able to explain any block of code in this repo.** Any member may be asked about
  any block.
