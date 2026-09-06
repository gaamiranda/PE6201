"""
The vendor seam. Exactly ONE function in this repository knows a vendor exists.

WHY IT IS ONE FUNCTION
    Switching model must be a string, or the D5(b) battery is not a comparison. Six people run
    the identical evaluation set and the identical v2 prompt with MODEL as the only thing that
    differs; if a vendor detail leaks into the loop or the tools, that guarantee is gone.

BACKEND = "scripted" IS THE DEFAULT AND MUST STAY THE DEFAULT
    A marker clones the repository and reproduces every number with no network and no key.
    D3(b) the guardrail checklist, D5(a) the end-to-end run and D7 both failures all run this
    way. If the harness does not run this way, Technical Execution is capped.

WHO OWNS WHAT
    The seam and the scripted dispatch: Goncalo / ZHENG (D1).
    The real replay backend over the whole evaluation set: JIN CHENG / NIU TONG (D5a) —
    it replaces _scripted_complete below and dev_transcripts.py goes away with it.
    The live path: needed by all six on 11 Sep for the battery. Marked TODO below.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from contracts import BACKEND, BASE_URL, MODEL  # noqa: F401  (re-exported: one config block)
from dev_transcripts import DEV_TRANSCRIPTS


class BackendError(Exception):
    """The backend could not produce a response. Distinct from ToolError: this is the model
    being unreachable, not a tool declining to answer."""


# ─────────────────────────────────────────────────────────────────────────────
# Prices. Used to turn a token count into the cost_usd that D6 and D7 both read.
#
# ⚠ VERIFY EVERY ROW ON openrouter.ai/models BEFORE THE 11 SEP BATTERY. Prices move, and a
# wrong number here silently corrupts the cost model rather than raising anything.
# USD per 1,000,000 tokens, (input, output).
# ─────────────────────────────────────────────────────────────────────────────

PRICES: Dict[str, tuple] = {
    "openai/gpt-4o-mini":                 (0.15, 0.60),
    "google/gemini-2.0-flash-001":        (0.10, 0.40),
    "meta-llama/llama-3.3-70b-instruct":  (0.12, 0.30),
    "deepseek/deepseek-chat":             (0.14, 0.28),
    "anthropic/claude-haiku-4.5":         (1.00, 5.00),
    "scripted":                           (0.00, 0.00),
}


def price(model: str, tokens_in: int, tokens_out: int) -> float:
    """Cost of one model call. Unknown model ids cost 0.0 and are NOT silently swallowed."""
    if model not in PRICES:
        raise BackendError(
            f"no price for model {model!r}. Add it to PRICES from openrouter.ai/models "
            f"before running a battery — an unpriced run corrupts D6."
        )
    pin, pout = PRICES[model]
    return (tokens_in * pin + tokens_out * pout) / 1_000_000


def estimate_tokens(text: str) -> int:
    """Rough token count for the scripted backend only.

    ~4 characters per token. This is an ESTIMATE and it is labelled as one wherever it is
    reported: the brief asks for tokens read from the API usage block, and on a live run that
    is what `complete` returns. The scripted backend has no usage block, so D7's before/after
    tables compare estimates against estimates — which is valid, because the failure is built
    as a deletion and both sides are measured the same way.
    """
    return max(1, len(text) // 4)


# ─────────────────────────────────────────────────────────────────────────────
# The one function.
# ─────────────────────────────────────────────────────────────────────────────

def complete(messages: List[Dict[str, str]], *, model: str = MODEL,
             backend: Optional[str] = None, case_id: Optional[str] = None,
             turn: Optional[int] = None) -> Dict:
    """Ask the model for one response.

    RETURNS  {"text": str, "tokens_in": int, "tokens_out": int, "estimated": bool}
             `estimated` is True when the counts did not come from a provider usage block —
             the loop carries the flag into the record so no table quotes an estimate as a
             measurement.
    """
    which = backend or BACKEND
    if which == "scripted":
        return _scripted_complete(messages, case_id=case_id, turn=turn)
    if which == "openrouter":
        return _openrouter_complete(messages, model=model)
    raise BackendError(f"unknown backend {which!r}")


def _scripted_complete(messages: List[Dict[str, str]], *, case_id: Optional[str],
                       turn: Optional[int]) -> Dict:
    """Deterministic replay. No network, no key, same answer every time.

    PLACEHOLDER — JIN CHENG / NIU TONG (D5a) replace this with a replay over the whole
    evaluation set. It currently reads dev_transcripts.py, which covers three claims.
    """
    key = (case_id, turn)
    if key not in DEV_TRANSCRIPTS:
        raise BackendError(
            f"no scripted response for case {case_id!r} turn {turn}. "
            f"dev_transcripts.py covers {sorted({c for c, _ in DEV_TRANSCRIPTS})} only — "
            f"this is the dev stub, not D5(a)."
        )
    text = DEV_TRANSCRIPTS[key]
    return {
        "text": text,
        "tokens_in": sum(estimate_tokens(m["content"]) for m in messages),
        "tokens_out": estimate_tokens(text),
        "estimated": True,
    }


def _openrouter_complete(messages: List[Dict[str, str]], *, model: str) -> Dict:
    """The live path — the ONLY place in this repository that spends money.

    temperature=0 is not a preference: without it a passing case can flip between runs and the
    battery stops being a comparison. Tokens come from the provider's usage block, never
    estimated, which is what makes the D5(b) numbers quotable as measurements.
    """
    import requests
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise BackendError("OPENROUTER_API_KEY not set. It lives in .env, which is gitignored.")
    try:
        r = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "messages": messages,
                  "temperature": 0, "max_tokens": 1024},
            timeout=90,
        )
    except Exception as exc:
        raise BackendError(f"request failed: {exc}")
    if r.status_code != 200:
        raise BackendError(f"HTTP {r.status_code}: {r.text[:300]}")
    d = r.json()
    if "choices" not in d:
        raise BackendError(f"no choices in response: {str(d)[:300]}")
    usage = d.get("usage", {})
    return {
        "text": d["choices"][0]["message"]["content"] or "",
        "tokens_in": usage.get("prompt_tokens", 0),
        "tokens_out": usage.get("completion_tokens", 0),
        "estimated": False,
    }
