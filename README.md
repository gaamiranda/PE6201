# PE6201 A2 — Applied AI System

Team **7**, Section **B** · Problem **A — health-insurance claim first response**

A single-agent ReAct system that reads an incoming claim, looks the facts up in local fixture data,
and reaches one of three outcomes — **approve in principle**, **request a specific missing
document**, or **escalate to a human assessor** — behind an autonomy gate on the one irreversible
step, issuing the decision.

This repository holds the agent, the tool layer, the guardrails, the evaluation set, the harness,
the fixtures, the result tables and the cost model. **All of the numbers live here**; the report
argues about them.

**Team members: start with [`PLAN.md`](PLAN.md).** It says what you own, who you are waiting on,
and by when.

---

## Status — 17 September 2026

Everything below runs from a clean clone, offline, with no API key. The numbers in the report are
the numbers this repository prints.

| | Status |
|---|---|
| The reference data, the answer key and `check_my_data.py` | ✅ runnable |
| The evaluation set — **42 cases, 17 negative, 76 trials** | ✅ closed |
| The agent: loop, tool layer, guardrails (`src/`) | ✅ committed |
| The evaluation harness and the scripted run (`harness/`) | ✅ 28 tests, reproduces below |
| Result tables (`results/`) | ✅ committed |
| The live battery across six models (D5(b)) | 🚧 runs 18 Sep — [`docs/D5b-runbook.md`](docs/D5b-runbook.md) |
| The report — six sections, 2,000 words | 🚧 in draft — [`PLAN.md` §6](PLAN.md) |

**One guardrail case fails and is meant to.** Row 2 of
[`evaluation/guardrail-checklist.md`](evaluation/guardrail-checklist.md) — a prompt injection that
imitates a tool result — is not caught: the agent approves `CLM-8952`. It is reported rather than
hidden, because a checklist that passes everything is not evidence of anything. See
[`docs/D7-failures.md`](docs/D7-failures.md).

---

## Check the data (works today, no network, no key)

```bash
git clone https://github.com/gaamiranda/PE6201.git
cd PE6201/A2_reference_data

python3 make_fixtures_A.py      # regenerates data_A/ from the generator
python3 check_my_data.py        # → "Your data hangs together."
```

Standard library only. No arguments, no packages to install.

## Reproduce our numbers

No network, no key, no cost. `BACKEND = "scripted"` is the default and replays a committed
transcript, so every figure below comes back byte-identical on any machine.

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python3 -m unittest discover -s harness -p 'test_*.py'      # 28 tests, offline

python3 harness/run_eval.py \
  --backend scripted \
  --judgements results/evaluations/eval-scripted-v2-final.judgements-reviewed.jsonl \
  --output-dir results/evaluations \
  --run-id yourname
```

Expected tail — diff against this:

```
Cases: 42 unique; 25 ordinary; 17 negative (7 request_document, 10 escalate)
Trials: 25 ordinary + 51 negative = 76 total
Code checks: 42 cases / 76 trials
Provisional code-only rate: 63/76 (82.89%)
Provisional negative code-only rate: 39/51 (76.47%)
Final combined pass rate: 57/76 (75.00%)
Final negative pass rate: 36/51 (70.59%)
Decision-only sanity rate: 72/76 (94.74%) across weighted trials
Decision-only case rate: 40/42 (95.24%) across unique cases
Tokens: 785906 in; 46280 out
Actual spend: US$0.00
Projected cost, 42-case single pass: US$0.058572
Projected cost, formal 76-trial schedule: US$0.097096
Median turns: 5.0; caps fired: 0; runtime errors: 0
Provisional code-failed case IDs: CLM-8888, CLM-8894, CLM-8952, CLM-8960, CLM-9002
```

**Three rates, and they are not interchangeable.** **63/76** is the code check alone. **57/76** is
the one to quote — code *and* human judgement, which six cases require. **40/42** is decisions only,
ignoring whether the record named the facts it had to name. A bare `python3 harness/run_eval.py`
with no `--judgements` prints `INCOMPLETE`, deliberately: fresh trials carry no judgement verdicts,
and the harness refuses to pass the code-only rate off as the final one.

The scripted backend replays deterministic canned responses. **It must stay the default**: if the
harness does not run this way, Technical Execution is capped.

### What runs free, and what costs money

Only **D5(b)**, the live battery, spends anything. **D3(b)** (the ten guardrail cases), **D5(a)**
(the reproducible end-to-end run) and **D7** (both failure reproductions) all run on the scripted
backend. If you find yourself spending live tokens on any of those three, stop.

### Running the live battery (costs credit)

```bash
# the key lives in .env at the repository root, which is gitignored — never commit it
cp .env.example .env && $EDITOR .env

python3 harness/run_eval.py --backend openrouter --model <model-id> --run-id <yourname-model>
```

Every member runs one live model on their own key, off the frozen `battery-v2.1` tag.
**[`docs/D5b-runbook.md`](docs/D5b-runbook.md) is the procedure** — who runs which model, the exact
commands, and the free checks to run before spending anything. The two conditions that make the
comparison valid are in [`PLAN.md` §4](PLAN.md).

---

## Repository map

| Path | What is in it | Deliverable |
|---|---|---|
| **[`PLAN.md`](PLAN.md)** | **Who does what, who waits on whom, the dates** | — |
| [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md) | Who did what — the commit history corroborates it | — |
| `src/` | The agent: the ReAct loop, the tool layer, the guardrail layer | D1, D2, D3(a) |
| `harness/` | Evaluation runner, graders, backends, instrumentation | D4, D5 |
| `A2_reference_data/` | The instructor's data package — generator, `data_A/`, **the answer key**, `check_my_data.py` | D4 |
| `evaluation/cases/README.md` | How to write and label an evaluation case | D4 |
| `evaluation/guardrail-checklist.md` | The ≥10 guardrail cases (separate from the eval set) | D3(b) |
| `results/` | Run outputs, result tables, turn distributions, cost tables | D4, D5, D6, D7 |
| `docs/` | The written deliverables the report is built from | D0, D2, D3, D4, D6, D7 |
| [`docs/D5b-runbook.md`](docs/D5b-runbook.md) | How each member runs their live battery | D5(b) |

**There is no `fixtures/` directory.** The fixture data is `A2_reference_data/`, and it stays
where it is — both scripts anchor on their own path, so the generator, the checker, `data_A/` and
the answer key must remain siblings. See [`docs/D4-data-and-cases.md`](docs/D4-data-and-cases.md).

**There is one answer key**, `A2_reference_data/expected_outcomes_A.json`, and it is a submitted
artefact. Do not start a second one.

## Build order

The brief's order, and the order we work in:

1. **D0** — why an agent at all ([`docs/D0-why-an-agent.md`](docs/D0-why-an-agent.md)). **Writing, no code.**
   The five "what good looks like" statements are committed **before the first agent commit**.
2. **D2(a), D2(b)** — the tool set and the six-field descriptors ([`docs/D2-tool-layer.md`](docs/D2-tool-layer.md)). **Design, no code.**
3. **D1, D2(c)** — the loop and multi-tool turns (`src/`).
4. **D3** — guardrails in code, then the checklist.
5. **D4** — the evaluation set (everyone, see [`PLAN.md` §3](PLAN.md)).
6. **D5** — scripted run, then the live battery.
7. **D6, D7** — cost model and the two reproduced failures.

## House rules

Full list in [`PLAN.md` §7](PLAN.md). The three that matter most:

- **Commit under your own account** — individual marks are adjusted against this history.
- **Never edit or delete a row the instructor shipped** — new ids only, inside your block.
- **Never commit a key** — `.env` is gitignored; keep it that way.

## Deadlines

| Date | What |
|---|---|
| **Thu 17 Sep, 23:59** | 🔒 Freeze — `battery-v2.1` tagged. Eval set, v2 prompt and harness final |
| **Fri 18 Sep** | Everyone runs their live battery off that tag |
| **Sat 19 Sep** | D6 actuals · result tables · six report sections assembled · demo recorded |
| **Sun 20 Sep, 23:59 SGT** | A2 due — repo, code copy in the NTULearn folder, report, demo link, self-appraisal |
| Wed 23 Sep, 23:59 SGT | Peer rating (participation requirement) |
