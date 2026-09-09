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
import json
from pathlib import Path

from typing import Dict, List, Optional

from contracts import BACKEND, BASE_URL, MODEL  # noqa: F401  (re-exported: one config block)

TRANSCRIPTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "evaluation"
    / "transcripts.jsonl"
)

_RECORDED_TRANSCRIPTS: Optional[Dict[tuple[str, int], str]] = None

# Recording is OPT-IN and must stay that way. evaluation/record_transcripts.py sets it True
# for the one pass that builds the recording; nothing else may.
#
# WHY: _load_recorded_transcripts() refuses a file holding two replies for the same
# (case_id, turn) — correctly, because a duplicate makes the replay ambiguous. If every live
# call appended, the D5(b) battery on 11 September would append a second copy of all 380 rows
# and the scripted backend would stop loading with "duplicate transcript response". D5(a),
# D3(b) and D7 all replay through it, and six members run live that day: the repository would
# break on the first one and stay broken through submission.
RECORD_TRANSCRIPTS = False


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
    "google/gemini-2.5-flash-lite":       (0.10, 0.40),   # the D5(a) recording model
    "mistralai/mistral-medium-3":         (0.40, 2.00),
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

def _append_transcript(case_id: str, turn: int, text: str) -> None:
    """Append one exact model reply to the JSONL recording."""
    TRANSCRIPTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "case_id": case_id,
        "turn": turn,
        "text": text,
    }

    with TRANSCRIPTS_PATH.open("a", encoding="utf-8", newline="\n") as file:
        json.dump(record, file, ensure_ascii=False)
        file.write("\n")


def _expected_case_count() -> int:
    """How many cases the recording must cover — read from the answer key, never hard-coded,
    so adding a case fails loudly here instead of quietly shrinking the evaluation."""
    key = TRANSCRIPTS_PATH.parent.parent / "A2_reference_data" / "expected_outcomes_A.json"
    return len({row["case_id"] for row in json.loads(key.read_text(encoding="utf-8"))})


def _load_recorded_transcripts() -> Dict[tuple[str, int], str]:
    """Load and validate the recorded OpenRouter replies once."""
    global _RECORDED_TRANSCRIPTS

    if _RECORDED_TRANSCRIPTS is not None:
        return _RECORDED_TRANSCRIPTS

    if not TRANSCRIPTS_PATH.exists():
        raise BackendError(
            f"recorded transcript file not found: {TRANSCRIPTS_PATH}"
        )

    transcripts: Dict[tuple[str, int], str] = {}

    with TRANSCRIPTS_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise BackendError(
                    f"invalid JSON in {TRANSCRIPTS_PATH} "
                    f"at line {line_number}: {error}"
                ) from error

            case_id = record.get("case_id")
            turn = record.get("turn")
            text = record.get("text")

            if not isinstance(case_id, str) or not case_id:
                raise BackendError(
                    f"invalid case_id at transcript line {line_number}"
                )
            if not isinstance(turn, int) or turn < 1:
                raise BackendError(
                    f"invalid turn at transcript line {line_number}"
                )
            if not isinstance(text, str):
                raise BackendError(
                    f"invalid text at transcript line {line_number}"
                )

            key = (case_id, turn)
            if key in transcripts:
                raise BackendError(
                    f"duplicate transcript response for "
                    f"case {case_id!r}, turn {turn}"
                )

            # Preserve the provider response exactly, including empty strings.
            transcripts[key] = text

    expected = _expected_case_count()
    case_count = len({case_id for case_id, _ in transcripts})
    if case_count != expected:
        raise BackendError(
            f"the recording covers {case_count} cases but the answer key holds {expected}. "
            f"Re-record the missing ones with evaluation/record_transcripts.py — a partial "
            f"recording silently drops cases from every scripted number."
        )
    if not transcripts:
        raise BackendError("the recorded transcript file is empty")

    _RECORDED_TRANSCRIPTS = transcripts
    return transcripts

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
        return _scripted_complete(
            messages,
            case_id=case_id,
            turn=turn,
        )

    if which == "openrouter":
        return _openrouter_complete(
            messages,
            model=model,
            case_id=case_id,
            turn=turn,
        )

    raise BackendError(f"unknown backend {which!r}")


def _scripted_complete(
    messages: List[Dict[str, str]],
    *,
    case_id: Optional[str],
    turn: Optional[int],
) -> Dict:
    """Replay an exact recorded reply without network access."""
    if case_id is None or turn is None:
        raise BackendError(
            "scripted replay requires both case_id and turn"
        )

    transcripts = _load_recorded_transcripts()
    key = (case_id, turn)

    if key not in transcripts:
        available_turns = sorted(
            recorded_turn
            for recorded_case, recorded_turn in transcripts
            if recorded_case == case_id
        )
        raise BackendError(
            f"no recorded response for case {case_id!r}, turn {turn}. "
            f"Available turns: {available_turns}"
        )

    text = transcripts[key]
    return {
        "text": text,
        "tokens_in": sum(
            estimate_tokens(message["content"])
            for message in messages
        ),
        "tokens_out": estimate_tokens(text),
        "estimated": True,
    }


def _openrouter_complete(
    messages: List[Dict[str, str]],
    *,
    model: str,
    case_id: Optional[str],
    turn: Optional[int],
) -> Dict:
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
        raise BackendError(
            f"no choices in response: {str(d)[:300]}"
        )

    usage = d.get("usage", {})
    text = d["choices"][0]["message"]["content"] or ""

    if RECORD_TRANSCRIPTS:
        if case_id is None or turn is None:
            raise BackendError(
                "live replies must include case_id and turn for transcript recording"
            )
        _append_transcript(case_id, turn, text)

    return {
        "text": text,
        "tokens_in": usage.get("prompt_tokens", 0),
        "tokens_out": usage.get("completion_tokens", 0),
        "estimated": False,
    }
