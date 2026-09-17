"""Run ONE case and print the ReAct trajectory, for the demo recording.

Deliberately not part of the evaluation path: it grades nothing and writes nothing. It exists so
slots 2 and 3 of the demo can SHOW the loop rather than describe it, which is what the brief asks
for. Scripted is the default, so a clip can be re-recorded as many times as it takes for free, and
it replays the committed transcript — the run on screen is the run in the results table.

    python3 evaluation/demo_one_case.py CLM-8941
    python3 evaluation/demo_one_case.py CLM-8941 --backend openrouter --model openai/gpt-4o-mini
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))

import loop  # noqa: E402

BOLD, DIM, OFF = "\033[1m", "\033[2m", "\033[0m"


def _fmt_call(name: str, args: tuple, kwargs: dict) -> str:
    parts = [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
    return f"{name}({', '.join(parts)})"


def main() -> None:
    ap = argparse.ArgumentParser(description="Run one case and print its trajectory")
    ap.add_argument("case_id")
    ap.add_argument("--backend", default="scripted", choices=("scripted", "openrouter"))
    ap.add_argument("--model", default=None)
    ap.add_argument("--prompt-version", default="v2", choices=("v1", "v2"))
    ap.add_argument("--width", type=int, default=100, help="observation truncation width")
    a = ap.parse_args()

    trace: list = []
    kw = {"prompt_version": a.prompt_version, "backend": a.backend, "trace": trace}
    if a.model:
        kw["model"] = a.model

    print(f"\n{BOLD}{a.case_id}{OFF}  ({a.backend}, prompt {a.prompt_version})\n")
    record = loop.run_case(a.case_id, **kw)

    for turn in trace:
        print(f"{BOLD}Round {turn.index}{OFF}")
        print(f"  {BOLD}Thought{OFF}      {turn.thought.strip()}")
        for (name, args, kwargs), obs in zip(turn.calls, turn.observations):
            one = " ".join(str(obs).split())
            if len(one) > a.width:
                one = one[: a.width - 1] + "…"
            print(f"  {BOLD}Action{OFF}       {_fmt_call(name, args, kwargs)}")
            print(f"  {BOLD}Observation{OFF}  {DIM}{one}{OFF}")
        print()

    print(f"{BOLD}Final{OFF}")
    body = dict(record)          # DecisionRecord is a TypedDict — already a plain dict
    usage = body.pop("usage", None)
    print("  " + json.dumps(body, indent=2, default=str, ensure_ascii=False).replace("\n", "\n  "))
    if usage:
        u = dict(usage)
        print(f"\n{BOLD}Cost{OFF}  {u.get('turns')} turns · {body.get('model_calls')} model calls · "
              f"{u.get('tokens_in')} in / {u.get('tokens_out')} out · "
              f"US${float(u.get('cost_usd') or 0):.6f}"
              f" · {body.get('unproductive_rounds', 0)} unproductive"
              f"\n      tools: {', '.join(u.get('tools_called') or []) or 'none'}"
              + (f" · cap fired: {u['cap_fired']}" if u.get("cap_fired") else ""))
    print()


if __name__ == "__main__":
    main()
