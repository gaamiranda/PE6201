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

## ⚠️ Status — 4 September 2026

The build is in progress. What a stranger can run today, and what is not there yet:

| | Status |
|---|---|
| The reference data, the answer key and `check_my_data.py` | ✅ present and runnable |
| The evaluation set (15 of a target 40 cases labelled) | 🚧 in progress — [`PLAN.md` §3](PLAN.md) |
| The agent, the tool layer, the guardrails (`src/`) | 🚧 not yet committed |
| The evaluation harness and the scripted run (`harness/`) | 🚧 not yet committed — due 8 Sep |
| Result tables (`results/`) | 🚧 empty until the runs happen |

This block is deleted, and the reproduce section below filled in, once the harness lands.

---

## Check the data (works today, no network, no key)

```bash
git clone https://github.com/gaamiranda/PE6201.git
cd PE6201/A2_reference_data

python3 make_fixtures_A.py      # regenerates data_A/ from the generator
python3 check_my_data.py        # → "Your data hangs together."
```

Standard library only. No arguments, no packages to install.

## Reproduce our numbers (once the harness lands)

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m harness.run_eval                            # BACKEND="scripted" is the default
```

<!-- TODO (JIN CHENG / NIU TONG, by 8 Sep): paste the expected tail of this output so a marker
     can diff against it — cases, trials, pass rate, median turns, total cost. -->

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

Every member runs one live model on their own key, off the frozen `battery-v2` tag. Who runs which
model, and the two conditions that make the comparison valid, are in [`PLAN.md` §4](PLAN.md).

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

Full list in [`PLAN.md` §6](PLAN.md). The three that matter most:

- **Commit under your own account** — individual marks are adjusted against this history.
- **Never edit or delete a row the instructor shipped** — new ids only, inside your block.
- **Never commit a key** — `.env` is gitignored; keep it that way.

## Deadlines

| Date | What |
|---|---|
| **Thu 17 Sep, 23:59** | 🔒 Freeze — `battery-v2` tagged. Eval set, v2 prompt and harness final |
| **Fri 18 Sep** | Everyone runs their live battery off that tag |
| **Sun 20 Sep, 23:59 SGT** | A2 due — repo, code copy in the NTULearn folder, report, demo link, self-appraisal |
| Wed 23 Sep, 23:59 SGT | Peer rating (participation requirement) |
