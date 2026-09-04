# PE6201 A2 — Applied AI System

Team **[TEAM ID]**, Section **[A/B/C]** · Problem **[A — health-insurance claim first response / B — outpatient referral coordination]**

A single-agent ReAct system that reads an incoming [claim / referral], looks facts up in local
fixture data, and reaches one of three outcomes — **act**, **ask for a specific missing item**, or
**escalate to a human** — behind an autonomy gate on the one irreversible step.

This repository holds the agent, the tool layer, the guardrails, the evaluation set, the harness,
the fixtures, the result tables and the cost model. **All of the numbers live here**; the report
argues about them.

---

## Reproduce our numbers (no network, no API key, no cost)

```bash
git clone https://github.com/gaamiranda/PE6201.git
cd PE6201
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m harness.run_eval                            # BACKEND="scripted" is the default
```

<!-- TODO: replace the command above with the real entry point once the harness exists,
     and paste the expected tail of the output here so a marker can diff against it. -->

Expected output:

```
TODO: paste the summary table the scripted run prints —
      cases, trials, pass rate, median turns, total cost.
```

The scripted backend replays deterministic canned responses. **It must stay the default**: if the
harness does not run this way, Technical Execution is capped.

### What runs free, and what costs money

Only **D5(b)**, the live battery, spends anything. **D3(b)** (the ten guardrail cases), **D5(a)**
(the reproducible end-to-end run) and **D7** (both failure reproductions) all run on the scripted
backend. If you find yourself spending live tokens on any of those three, stop.

### Running the live battery (costs credit)

```bash
export OPENROUTER_API_KEY=...        # never commit this
python -m harness.run_eval --backend openrouter --model <model-id>
```

**Every member runs one live model on their own key.** Three models is the floor; for a team of N,
**N − 1 models plus one member running the v1 prompt pass** is what is expected — so five models and
a v1 pass in a team of six. At 56 runs on the cheap tier that is about **US$0.27 each**, so six
models costs the team no more per person than three.

Two conditions, or the comparison means nothing: the models must span **at least two price tiers**,
and **no two members may pick models from the same family**. Everyone runs the identical evaluation
set and the identical v2 prompt — the model name is the only thing that differs.

---

## Repository map

| Path | What is in it | Deliverable |
|---|---|---|
| `src/` | The agent: the ReAct loop, the tool layer, the guardrail layer | D1, D2, D3(a) |
| `harness/` | Evaluation runner, graders, backends, instrumentation | D4, D5 |
| `evaluation/cases/` | The evaluation cases, **one file per author** — 40 with 8 negative is the expected shape | D4 |
| `evaluation/guardrail-checklist.md` | The ≥10 guardrail cases (separate from the eval set) | D3(b) |
| `fixtures/` | Local JSON/CSV data files the tools read | — |
| `results/` | Run outputs, result tables, turn distributions, cost tables | D4, D5, D6, D7 |
| `docs/` | The written deliverables the report is built from | D0, D2, D3, D6, D7 |
| `CONTRIBUTIONS.md` | Who did what — the commit history must corroborate it | — |

## Build order

The brief's order, and the order we work in:

1. **D0** — why an agent at all (`docs/D0-why-an-agent.md`). **Writing, no code.**
   The five "what good looks like" statements must be committed **before the first agent commit**.
2. **D2(a), D2(b)** — the tool set and the six-field descriptors (`docs/D2-tool-layer.md`). **Design, no code.**
3. **D1, D2(c)** — the loop and multi-tool turns (`src/`).
4. **D3** — guardrails in code, then the checklist (`src/`, `evaluation/guardrail-checklist.md`).
5. **D4** — the evaluation set (`evaluation/cases/`).
6. **D5** — scripted run, then the live battery.
7. **D6, D7** — cost model and the two reproduced failures.

## House rules

- **Commit under your own account.** Run this once before your first commit:
  ```bash
  git config user.name "Your Name"
  git config user.email "the-email-on-your-github-account"
  ```
  A commit with an unrecognised email does not link to your profile and does not appear in the
  contributors graph. Individual marks are adjusted against this history.
- **Never commit a key.** `.env` is gitignored; keep it that way.
- **Evaluation cases go in your own file** under `evaluation/cases/`. Six people editing one JSON
  array is a guaranteed merge conflict.
- **Never edit or delete a fixture row the instructor shipped.** Add new rows with new ids, and run
  `check_my_data.py` over your additions.
- **Keep the agent in `.py` modules,** not in one big notebook. Notebook merges are brutal with
  seven contributors.
- **Update `CONTRIBUTIONS.md` as you go,** not on the 13th.

## Deadlines

| Date | What |
|---|---|
| Wed 2 Sep, midday | Reference data, data guide, `check_my_data.py` and the starter scaffold land on NTULearn |
| Fri 4 Sep, 23:59 SGT | Team declaration due — **the instructor's `TEAM_DECLARATION.docx` template**, in the NTULearn folder |
| Sun 13 Sep, 23:59 SGT | A2 due — repo, code copy in the folder, report, demo link, self-appraisal |
| Wed 16 Sep, 23:59 SGT | Peer rating (participation requirement) |
