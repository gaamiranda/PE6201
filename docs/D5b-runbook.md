# D5(b) — the live battery runbook

**Owner:** NIU TONG. *Assignment, dates and dependencies: [`../PLAN.md`](../PLAN.md).*

One page, six people, one day. Read it before Friday, not on Friday.

> **The whole point of D5(b) is a comparison.** Six batteries are only comparable if the model id
> is the *only* thing that differed between them. Everything in §1 exists to protect that, and
> every step in §3 exists so Friday costs you twenty minutes instead of a day.

---

## 1 · What you must not change

- the cases · the answer key · the prompt · the tool descriptors · the tools · the guardrails
- temperature or any other runtime parameter (`temperature=0` is set in `src/backends.py`; without
  it a passing case can flip between runs and the battery stops being a comparison)

**Everyone runs the same commit — the `battery-v2.1` tag.** During the comparison the only things
that may differ between two members are the **model id** and, for ZHENG YONGJIE alone, the
**prompt version**.

You do not have to be trusted on this and you are not asked to be: the harness stamps the git
commit SHA into every trial row it writes. See §7.

---

## 2 · Who runs what

| Member | Model | Family | Tier | Projected, 76 trials |
|---|---|---|---|---|
| Goncalo Miranda | `openai/gpt-4o-mini` | OpenAI | cheap | US$0.146 |
| JIN CHENG | `google/gemini-2.5-flash-lite` | Google | cheap | US$0.097 |
| NIU TONG | `meta-llama/llama-3.3-70b-instruct` | Meta | cheap | US$0.093 |
| SUN YUCONG | `deepseek/deepseek-chat` | DeepSeek | cheap† | US$0.250 |
| WANG HONGJUN | `mistralai/mistral-medium-3` | Mistral | **mid** | US$0.407 |
| ZHENG YONGJIE | **v1 prompt pass** on `openai/gpt-4o-mini` | — | cheap | US$0.146 |

> ⚠️ **JIN CHENG's model changed on 17 September.** `google/gemini-2.0-flash-001` was **delisted** —
> there is no `google/gemini-2.0-*` on OpenRouter at all — and a live run against it returns a 404
> on the first call. He runs **`google/gemini-2.5-flash-lite`**, the only cheap Gemini remaining.
> That is also the model the D5(a) transcripts were recorded from, which makes his battery a direct
> live-versus-replay comparison on one model: a free result for D6, not a problem.
>
> **† DeepSeek's price nearly doubled the projection.** The table had `(0.14, 0.28)`; the live rate
> is `(0.2574, 1.0287)`, so SUN YUCONG's schedule goes from US$0.123 to **US$0.250**. It now sits
> between gpt-4o-mini and Mistral, so the "cheap" label is arguable — the two-tier condition is met
> by Mistral either way. Nothing about her runs changes; only what they cost.
>
> Both were found by the freeze-checklist price check on 17 September, against OpenRouter's own
> price feed rather than a reading of the web page. `meta-llama/llama-3.3-70b-instruct` moved too
> — `(0.12, 0.30)` to `(0.10, 0.32)` — which makes NIU TONG's battery slightly cheaper.

> ⚠️ **WANG HONGJUN is on Mistral, not Anthropic.** He moved off `anthropic/claude-haiku-4.5` on
> 8 September: it came to roughly **US$3.75** over our schedule and broke our own US$3 rule. If you
> are holding an older copy of this table, it is wrong. The reasoning is in
> [`../CONTRIBUTIONS.md`](../CONTRIBUTIONS.md).

Five families, two price tiers — both required conditions met.

**These are projections, not quotes.** They price the scripted run's measured token counts
(785,906 in / 46,280 out over 76 trials) at each model's published rate. A chattier model takes
more turns and costs more. Treat them as a floor. The gap between projection and actual bill is
WANG HONGJUN's to report in D6.

---

## 3 · Before Friday — all free, none of it spends anything

**Do these this week.** Every one of them fails for free now and costs you a paid run on Friday.

**a. Get the code and install.**
```bash
git pull
pip install -r requirements.txt          # requests + python-dotenv
```

**b. Put your key in `.env` at the repository root.** Copy `.env.example`:
```
OPENROUTER_API_KEY=sk-or-...
```
`.env` is gitignored. Keep it that way.

**c. Run the battery on the scripted backend. It is free, offline, and needs no key.**
```bash
python3 -m unittest discover -s harness -p 'test_*.py'    # expect: 28 tests, OK
python3 harness/run_eval.py                                # scripted is the default
```
This proves your checkout, your Python and the harness all work, so that on Friday the **only**
new variable is your key. If something is broken, this is where you want to find out.

**d. Check your connection and your model id — one call, a fraction of a cent.**
```bash
python3 -c "
import sys; sys.path.insert(0,'src'); import backends
r = backends.complete([{'role':'user','content':'reply with the word ok'}],
                      model='YOUR-MODEL-ID', backend='openrouter')
print(r['text'][:40], '| in', r['tokens_in'], '| out', r['tokens_out'], '| estimated', r['estimated'])
"
```
You need **three** things from that line, which is why the snippet prints them:
1. text came back — the key works;
2. `tokens_in` / `tokens_out` are non-zero — the provider returned a usage block;
3. `estimated False` — the counts are measured, not guessed. **If it says `True`, stop and tell
   NIU TONG.** Estimated counts cannot be quoted as measurements in D6.

**Verify your model id on [openrouter.ai/models](https://openrouter.ai/models) first.** A wrong id
is an immediate `HTTP 400: ... is not a valid model ID`. It fails loudly and costs nothing, but it
fails *on call one of 76* — check it before, not during. No `:free` variants, no reasoning models.

**e. Confirm your key has credit.** 76 trials on the cheap tier is well under a dollar, but a key
with a zero balance fails the same way as no key at all.

---

## 4 · The run

> ⚠️ **The tag was re-cut as `battery-v2.1` on 17 September.** The first battery run off
> `battery-v2` — SUN YUCONG on `deepseek/deepseek-chat` — lost **61 of its 76 trials** to
> OpenRouter `HTTP 429` rate limits. The harness had no retry: a throttled call became a runtime
> error and the run moved straight to the next trial, which, because a failed call returns
> instantly, made it hit the endpoint *faster the more it was being throttled*. `v2.1` adds
> retry with backoff on the live path only. **If you ran off `battery-v2`, that run is void — run
> again off `v2.1`.** Nothing else changed, and every scripted number is identical.
>
> You will now see lines like `[backend] HTTP 429 ... — retry 1/4 in 1.7s` during a live run.
> That is the fix working; leave it alone. A run that still fails after five attempts records a
> runtime error, as before.
>
> **Salvage rule, added 19 September.** "Void" above was written to stop a member submitting a
> run that *lost trials to throttling*. It is not a statement about the commit hash. A
> `battery-v2` run is salvageable, and must be kept rather than repeated, when all three hold:
>
> 1. **The diff is transport-only.** `git diff battery-v2 battery-v2.1 -- src/ harness/ evaluation/`
>    returns exactly one file, `src/backends.py`, +51/−12, in two hunks: three added imports
>    (`random`, `sys`, `time`) and the failure branch of `_openrouter_complete`. No change to the
>    loop, the tools, the prompt, the scoring, or the judgement rule.
> 2. **`PRICES` is unchanged.** The two tables are byte-identical, so every projected cost is
>    computed from the same price model as the other five batteries.
> 3. **The run recorded zero runtime errors.** This is the one that matters. The retry only
>    executes when a request fails. A run that never failed a request never reached the changed
>    code, so re-running could not produce a more correct number — only a different one, because
>    the harness is non-deterministic at `temperature=0` (§3).
>
> **WANG HONGJUN's `mistralai/mistral-medium-3` battery is kept under this rule**, stamped
> `commit_id 61804e3`. It reported 0 runtime errors and 0 caps across all 76 trials. Re-running it
> would have discarded twelve completed human judgements and bought a *different* result, not a
> better one. Five batteries carry `8489267`; this one carries `61804e3`, and the reason is here.
>
> If any of the three conditions fails, the run is void as originally written. SUN YUCONG's first
> DeepSeek run fails condition 3 by 61 trials and is kept only as evidence of the defect.

**After the `battery-v2.1` tag is announced — not before.** A run off any other commit is void and
has to be paid for twice.

```bash
git fetch --tags && git checkout battery-v2.1

python3 harness/run_eval.py \
  --backend openrouter \
  --model meta-llama/llama-3.3-70b-instruct \
  --run-id niu-llama-70b \
  --output-dir results/evaluations
```

Substitute your own model from §2. **ZHENG YONGJIE alone adds `--prompt-version v1`:**
```bash
python3 harness/run_eval.py --backend openrouter \
  --model openai/gpt-4o-mini --prompt-version v1 \
  --run-id zheng-4omini-v1 --output-dir results/evaluations
```

**Always pass `--run-id <surname>-<model>`.** Without it the run is named by UTC timestamp and six
people's results become indistinguishable in one directory. The harness refuses to overwrite an
existing run rather than clobbering it, so a repeated `--run-id` is an error, not a silent loss.

### 76 runs, not 56

**25 ordinary cases × 1 trial + 17 negative cases × 3 trials = 76 trials** over 42 cases. The
harness expands this itself — you do not count anything. If your summary says a total other than
76, something is wrong; stop and say so.

### Your run will print `INCOMPLETE`. That is correct.

Fresh trials have no human judgement attached yet, so the combined score cannot yet be computed.
The harness refuses to print a number it cannot back up rather than quietly passing off the
code-only rate as the final one. You will still get your **code-only** rate immediately. See §6.

### If it dies partway

Do not restart blindly — you have already paid for the completed trials. Keep the partial output,
tell NIU TONG what the error was, and ask before re-running.

---

## 5 · The key

Your API key must never be: committed to GitHub · written into a notebook · written into a README
· included in a results file · pasted into the group chat.

It lives in `.env`, which is gitignored, and nowhere else. If you ever paste one by accident, say
so immediately and rotate it on openrouter.ai — a leaked key is someone else's bill.

---

## 6 · Judgement, and what you hand in

Six of the 42 cases are graded by a person as well as by code — **12 trials** in your battery. You
judge your own, while you still have the context.

**a.** Your run wrote a `*.judgement-queue.jsonl` next to your results. Open it and fill in
`judgement_pass` (true/false), `reviewer` (your name) and `reviewer_notes` (one line: what you saw)
on each of the 12 rows.

The rule, and it is not a matter of taste:

> A `must_record` fact counts if it appears anywhere in the Agent's **complete structured final
> record**. Facts appearing only in hidden transcript Thought content do not count.
> *(Confirmed 15 September 2026.)*

The queue row gives you the complete structured record — including `missing`, `lines_resolved`,
`trigger`, `escalate_to`, `approved_total`, `refused_total`. Judge **only** what is in that record.
Do not fill a gap from the fixtures, the case id, the transcript or the Thought text.

**b.** Combine them into your final number. **This spends nothing** — it re-grades the trials you
already paid for:
```bash
python3 harness/run_eval.py \
  --input-results results/evaluations/<your-run>.trials.jsonl \
  --judgements    results/evaluations/<your-run>.judgement-queue.jsonl \
  --run-id niu-llama-70b-final \
  --output-dir results/evaluations
```

**c. Commit your own results, under your own account.** All four files your run produced, plus the
filled judgement file. Individual marks are adjusted against the commit history — do not let
someone else commit your work for you.

**d. Then send NIU TONG:** your name, model, family, tier, prompt version, the commit SHA, the run
date, total runs, passed runs, overall rate, negative-case rate, tokens in, tokens out, total cost,
median turns, failed case ids, and anything that errored or was re-run.

**Do not send only a pass rate.** The raw per-trial file is the evidence; the rate is a summary of
it. Commit both.

---

## 7 · The field names — nothing here is filled in by hand

Every field is already in the `.trials.jsonl` your run writes. Some are named differently from how
we say them in conversation:

| Spoken as | Field in the file |
|---|---|
| decision | `actual_decision` |
| trigger | `actual_trigger` |
| pass | `final_pass` (`code_check_pass` before judgement) |
| input tokens / output tokens | `tokens_in` / `tokens_out` |
| cost | `actual_spend_usd` (live) · `estimated_cost_usd` |
| grader type | `check_type` (`code` or `code+judgement`) |
| test date | `evaluated_at_utc` |
| commit | `commit_id` |

Only `model_family` and `price_tier` are not in the file. They come from the table in §2 — NIU TONG
adds them once, rather than six people typing them.

**`commit_id` is stamped into every row automatically.** So the same-commit rule is checked, not
trusted:
```bash
python3 -c "
import json,glob,collections
c=collections.Counter()
for f in glob.glob('results/evaluations/*.trials.jsonl'):
    for line in open(f):
        c[(f.split('/')[-1][:40], json.loads(line)['commit_id'][:12])] += 1
for k,v in sorted(c.items()): print(v, k)
"
```
One distinct SHA across all six files, and the comparison holds. Two, and it does not.

---

## 8 · What runs free, and what costs money

| Free — scripted backend, no key | Costs credit |
|---|---|
| D3(b) the ten guardrail cases | **D5(b), this document** |
| D5(a) the reproducible end-to-end run | |
| D7 both failure reproductions | |
| combining judgements (§6b) | |

**Debug scripted.** If you are burning live tokens to find a bug, stop.
