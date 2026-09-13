# results/evaluations — raw harness output

**Owners:** JIN CHENG · NIU TONG. Written by `harness/run_eval.py`, never by hand.

`../README.md` lists the summary tables the report cites. This directory holds what those
tables are computed *from*: one set of files per evaluation run, kept so any figure in the
report can be traced back to the individual trials that produced it.

## What one run produces

| Suffix | What it holds |
|---|---|
| `.trials.jsonl` | One record per trial — 76 for a full battery. The raw evidence |
| `.judgement-queue.jsonl` | The trials awaiting a judgement check, emitted for a reviewer |
| `.judgements-reviewed.jsonl` | The reviewer's verdicts, with reviewer name and timestamp |
| `.judgements-applied.jsonl` | Audit trail of which judgement landed on which trial |
| `.summary.json` | The computed rates, costs, token totals and failure reasons |

## Naming

```
eval-<backend>-<model>-<prompt version>-<run id>.<suffix>
```

Per-run files are gitignored — they accumulate on every invocation and would churn every
diff. **Files named `eval-*-final.*` are committed**, and they are the ones the report cites.
Renaming a run to `-final` is the act of saying "this is the number we stand behind".

## What is committed today

`eval-scripted-v2-final.*` — the scripted baseline on `google/gemini-2.5-flash-lite`, v2
prompt, 42 cases / 76 trials. Reproduce it with no network and no API key:

```bash
python -m harness.run_eval
```

Two rates matter and they are far apart, which is the point:

- **90.48%** (38/42) of decisions match the answer key
- **64.47%** (49/76) survive once the judgement checks ask whether the record justifies the
  decision it reached

The gap is the finding, not a rounding difference. The agent decides well and explains badly.

## The rule

Every number in here is one **we ran**. A trial that failed stays in the file — a semantic
failure is a result, not a mistake to be rerun until it passes. Reruns are for technical
faults only, and the rerun records why.
