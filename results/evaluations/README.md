> ## ⚠️ The `eval-*-final.*` files are STALE as of 2026-09-15, and must not be quoted
>
> They were produced on 2026-09-12/13 and report **38/42 (90.48%) decisions and 49/76 (64.47%)
> combined**. The current code reports **40/42 (95.24%) and 63/76 (82.89%)**.
>
> Three prompt and parser defects were fixed on 15 September and all 42 transcripts were
> re-recorded, so every record in `eval-scripted-v2-final.trials.jsonl` is out of date.
>
> **The trials and summary can simply be regenerated. The judgements cannot.**
> `eval-scripted-v2-final.judgements-reviewed.jsonl` holds 12 human judgement calls by NIU TONG.
> The same 12 `(case_id, trial)` pairs are still queued and the `trial_id`s are unchanged, so the
> file still *applies* — which is the hazard: regenerating the trials and leaving this file in place
> would silently re-apply judgements to records that no longer say what was judged. **9 of the 12
> records changed their `reason` text.** `CLM-8925` is the clearest: the reason went from a wrong
> claim about pre-authorisation to the correct "exceeds the remaining annual limit", and all 12 of
> the standing judgements are failures.
>
> Re-review is NIU TONG's call, not a mechanical regeneration. Until then this directory has no
> authoritative combined pass rate, and `python -m harness.run_eval` correctly reports
> **INCOMPLETE**.

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
