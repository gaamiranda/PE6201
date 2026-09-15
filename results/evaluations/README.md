> ## Final scripted baseline — reviewed 15 September 2026
>
> The `eval-scripted-v2-final.*` files were regenerated from all 42 transcripts re-recorded on
> 15 September 2026. NIU TONG reviewed all 12 required judgement trials against their complete
> structured final records: 3 passed judgement and 9 failed. No judgements are missing.
>
> The authoritative combined result is **57/76 (75.00%)**. Scripted replay made no provider
> request and actual spend was **US$0.00**.

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

The canonical final artifacts use the `eval-scripted-v2-final.*` prefix. The trials file contains
all 76 trial-level Agent outputs, code-check results, and run metadata; the summary contains the
aggregate scripted metrics, judgement status, token estimates, and projected costs. The judgement
queue is the blank human-review form and the audit record of exactly what evidence was shown to the
reviewer, so its `judgement_pass` and `reviewer` fields are intentionally null. Completed reviewer
decisions are stored separately in `eval-scripted-v2-final.judgements-reviewed.jsonl`, while
`eval-scripted-v2-final.judgements-applied.jsonl` records exactly which completed judgement was
applied to each stable trial identity.

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
python3 harness/run_eval.py \
  --backend scripted \
  --judgements results/evaluations/eval-scripted-v2-final.judgements-reviewed.jsonl \
  --output-dir results/evaluations \
  --run-id final2
```

The final metrics are:

- **40/42 (95.24%)** decisions match the answer key across unique cases
- **63/76 (82.89%)** pass the provisional code-only check
- **57/76 (75.00%)** pass the complete code-plus-judgement check
- **36/51 (70.59%)** negative trials pass the complete check
- **3/12** required judgement trials pass; **9/12** fail; **0** are missing

The final run reports projected costs of **US$0.058572** for one 42-case pass and
**US$0.097096** for the formal 76-trial schedule. These are estimates derived from replayed token
usage, not measured API expenditure.

## Human judgement rule

> A must_record fact counts if it appears anywhere in the Agent’s complete structured final
> record. Facts appearing only in hidden transcript Thought content do not count. Rule confirmed
> 15 September 2026.

The reviewer may use structured fields such as `missing`, `lines_resolved`, `trigger`,
`escalate_to`, `approved_total`, and `refused_total`. Facts must not be inferred from fixtures,
case IDs, transcripts, or hidden Thought content. The review queue preserves the complete
structured final record used for each decision.

## The rule

Every number in here is one **we ran**. A trial that failed stays in the file — a semantic
failure is a result, not a mistake to be rerun until it passes. Reruns are for technical
faults only, and the rerun records why.
