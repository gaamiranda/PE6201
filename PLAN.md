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

From `TEAM_DECLARATION.docx`, unchanged:

| Member | Model | Family | Tier | ~56–60 runs |
|---|---|---|---|---|
| Goncalo Miranda | `openai/gpt-4o-mini` | OpenAI | cheap | ~US$0.30 |
| JIN CHENG | `google/gemini-2.0-flash-001` | Google | cheap | ~US$0.30 |
| NIU TONG | `meta-llama/llama-3.3-70b-instruct` | Meta | cheap | ~US$0.30 |
| SUN YUCONG | `deepseek/deepseek-chat` | DeepSeek | cheap | ~US$0.30 |
| WANG HONGJUN | `anthropic/claude-haiku-4.5` | Anthropic | **mid** | ~US$2.94 |
| ZHENG YONGJIE | **v1 prompt pass** on `openai/gpt-4o-mini` | — | cheap | ~US$0.30 |

Five families, two price tiers — both conditions met. Own key, own model, own numbers.

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

| Date | What | Who |
|---|---|---|
| **Fri 4 Sep** | Declaration filed ✅ · repo restructured · **D0(c) five statements written** | Goncalo, ZHENG YONGJIE |
| **Sat 5 Sep** | `src/contracts.py` frozen · case baton starts | Goncalo → the six |
| **Sun 6 Sep** | Tool set (D2a) + descriptors (D2b v1) drafted | Goncalo, ZHENG, SUN YUCONG |
| **Mon 7 / Tue 8 Sep** | Class 6 · loop + tools working · harness skeleton runs scripted | Goncalo, ZHENG, JIN CHENG, NIU TONG |
| **Tue 8 Sep** | Case baton finished — all 40 cases labelled, `check_my_data.py` clean | all six |
| **Wed 9 Sep** | Guardrail layer + 10-case checklist · D7 both failures reproduced | SUN YUCONG, JIN CHENG, NIU TONG |
| **Thu 10 Sep 23:59** | 🔒 **FREEZE.** Tag `battery-v2`. Eval set, v2 prompt and harness final. | Goncalo tags |
| **Fri 11 Sep** | **Everyone runs their live battery** off that tag, commits their numbers | all six |
| **Sat 12 Sep** | Cost model · result tables · six report sections drafted and assembled | WANG HONGJUN, ZHENG YONGJIE |
| **Sun 13 Sep** | Demo recorded (every member speaks) · self-appraisal · **submit by 23:59 SGT** | all six |
| Wed 16 Sep | Peer rating — participation requirement | all six |

**Thursday's freeze is the one date that cannot slip.** Six people running the battery off six
different commits silently voids the whole comparison.

### The 10 Sep freeze checklist

Things that are legitimately unanswerable today and become answerable the moment D4 and D5(a)
land. Each has a named owner and a document it has to be written back into — a deferred number is
a tracked dependency, not a free pass.

| # | What closes | Unblocked by | Written back into | Owner |
|---|---|---|---|---|
| 1 | **D0(b) reliability arithmetic** — measured `P`, median `T`, and our own `s = P^(1/T)`. Report §1 requires the figure, not the formula | D4 labels + the D5(a) run | `docs/D0-why-an-agent.md` and the D0 submission draft | ZHENG YONGJIE |
| 1b | **D0(a) turn counts** — CLM-8925 and CLM-8842 currently carry *predicted* turns from our dependency rule (2 and 5), labelled as such. Replace with measured medians. Note the brief's own worked example is 4, and live runs vary run to run — that variance is itself the R7 cost | the D5(a) run | the D0 submission draft | ZHENG YONGJIE |
| 2 | **`Guards.step_cap` and `budget_ceiling_usd`** — set from the measured turn distribution, not a round number | the D5(a) run | `src/loop.py` | SUN YUCONG |
| 3 | **D2(b) v1 → v2** — tokens per call, pass rate, guardrail cases, both measured | a working harness | `docs/D2-tool-layer.md` | SUN YUCONG |
| 4 | **D2(c) sequential vs parallel** — the real comparison, not the dev transcripts | D5(a) replay over the whole set | `docs/D2-tool-layer.md` | Goncalo, ZHENG YONGJIE |
| 5 | **`PRICES` re-verified** on openrouter.ai before anyone spends | — do it Thu | `src/backends.py` | WANG HONGJUN |

Item 1 is the one that gets discovered on the 13th if nobody owns it: D0 reads as finished, and the
gap is a single sentence deep inside it.

---

## 6 · House rules

- **Commit under your own account.** Individual marks are adjusted against the commit history,
  and section 8 says the log must be corroborated by it. Once, before your first commit:
  ```bash
  git config user.name "Your Name"
  git config user.email "the-email-on-your-github-account"
  ```
- **Add a line to `CONTRIBUTIONS.md` when something lands.** Not on the 13th.
- **Never commit a key.** `.env` is gitignored; keep it that way.
- **Never edit or delete a row the instructor shipped.** New ids only, inside your block.
  `check_my_data.py` fingerprints every shipped row and will name the one that moved.
- **No framework owning the loop** (LangChain, LangGraph, CrewAI, AutoGen). Ordinary libraries for
  everything else are fine.
- **`BACKEND = "scripted"` stays the default.** If the harness does not run that way,
  Technical Execution is capped.
- **You must be able to explain any block of code in this repo.** Any member may be asked about
  any block.
