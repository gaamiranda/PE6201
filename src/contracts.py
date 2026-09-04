"""
Contracts — the shapes every other part of A2 agrees on.

WHY THIS FILE EXISTS
--------------------
Four people are otherwise blocked on the agent loop being finished:

    harness (JIN CHENG, NIU TONG)  needs to know what a run returns
    descriptors (SUN YUCONG)       needs the tool signatures
    cost model (WANG HONGJUN)      needs turns / tokens_in / tokens_out / cost_usd

None of them actually needs the loop. They need its *types*. So the types land first, and
everybody codes against this file while the loop is still being written.

There is no behaviour in here on purpose. Nothing imports a vendor, nothing reads a file,
nothing calls a model. It is a contract.

FROZEN AFTER 5 SEPTEMBER — additive changes only.
If you need a field that is not here, add it and tell the team; do not rename or remove one,
because someone else has already written code against it.

WHERE THE SHAPES COME FROM
--------------------------
Appendix A of the brief, which gives the decision record for all three outcomes. The answer key
(A2_reference_data/expected_outcomes_A.json) is written against the same routing table, so
DecisionRecord.decision and ExpectedOutcome.expected_decision use the SAME three strings.
That is not a coincidence and it is what makes a code check possible.
"""

from typing import Dict, List, Literal, Optional, TypedDict

# ─────────────────────────────────────────────────────────────────────────────
# The three outcomes. Problem A's routing table allows exactly these and no others.
# ─────────────────────────────────────────────────────────────────────────────

Decision = Literal["approve_in_principle", "request_document", "escalate"]

# The single trigger that sent a claim to a human. Escalations only.
# A run that reaches the right outcome by the WRONG trigger is not a pass.
Trigger = Literal[
    "policy_lapsed",
    "outside_policy_dates",
    "annual_limit_exceeded",
    "duplicate_claim",
    "instruction_in_member_narrative",
]

# Suggest = proposes, human does it. Confirm = proposes, human approves, agent does it.
# Act = agent does it. The gate sits in front of the irreversible step, not the whole agent.
Autonomy = Literal["suggest", "confirm", "act"]

LineStatus = Literal["covered", "not_covered"]


# ─────────────────────────────────────────────────────────────────────────────
# What the agent produces. ONE of these per run. This is the marked artefact:
# "the record is the output of your agent — it is the thing that gets marked."
# ─────────────────────────────────────────────────────────────────────────────

class LineDisposition(TypedDict, total=False):
    """One claim line, decided. Every line gets one — that is what the routing table requires."""
    code: str                    # procedure code, e.g. "47120"
    amount: int                  # dollars, as it appears on the claim
    status: LineStatus
    preauth: Optional[str]       # e.g. "PA-5521 valid 2026-08-01..2026-10-31"
    exclusion: Optional[str]     # e.g. "EX-14 cosmetic dermatology" — required if not_covered


class MissingItem(TypedDict, total=False):
    """The named thing a request_document is asking for. NEVER 'more information'."""
    item: str                    # "pre-authorisation reference"
    for_line: str                # "62480"
    must_be_valid_on: str        # "2026-09-08"


class Usage(TypedDict):
    """Instrumentation. Without this a loop failure is invisible: it raises no exception,
    it just costs more. Recorded on EVERY run, not only the ones that act."""
    turns: int                   # T — passes around the loop in ONE run
    tokens_in: int               # read from the API usage block, not estimated
    tokens_out: int              # reasoning tokens land here too, if any
    cost_usd: float
    cap_fired: Optional[Literal["step_cap", "budget_ceiling", "dedup"]]
    tools_called: List[str]      # in order, e.g. ["get_claim", "lookup_policy", ...]


class DecisionRecord(TypedDict, total=False):
    """The gated action's output — one structured record appended to results/decisions.jsonl.

    It is NOT a letter. No greeting, no recipient, no policy summary, no template. The names are
    the business action; the code is a log line.
    """
    ts: str                      # ISO 8601
    case_id: str                 # joins to claims.json claim_id AND to the answer key
    decision: Decision
    reason: str                  # prose — this is the field a JUDGEMENT check reads

    # approve_in_principle
    lines: List[LineDisposition]
    approved_total: int
    refused_total: int

    # request_document
    missing: MissingItem
    lines_resolved: List[str]    # an ask still records what it DID resolve

    # escalate
    escalate_to: str             # "human claims assessor"
    trigger: Trigger             # exactly one

    # always
    evidence: List[str]          # ["get_claim", "lookup_policy", "check_coverage x3", ...]
    autonomy: Autonomy
    gate: str                    # "operator approved at turn 4" / "issue_decision_letter not called"
    usage: Usage


# ─────────────────────────────────────────────────────────────────────────────
# What the answer key holds. One row per case, ours and the instructor's alike.
# Source: A2_reference_data/expected_outcomes_A.json — see evaluation/cases/README.md.
# ─────────────────────────────────────────────────────────────────────────────

class ExpectedOutcome(TypedDict, total=False):
    case_id: str
    expected_decision: Decision
    trigger: Optional[Trigger]       # escalations only
    missing: Optional[MissingItem]   # requests only
    family: str                      # which case family this exercises
    must_record: List[str]           # what a full-marks record carries beyond the decision
    note: str                        # why this case is here


# ─────────────────────────────────────────────────────────────────────────────
# What the harness produces per trial.
# ─────────────────────────────────────────────────────────────────────────────

CheckKind = Literal["code", "judgement"]


class TrialResult(TypedDict, total=False):
    case_id: str
    trial: int                   # 1 for ordinary cases; 1..3 for negative cases
    model: str                   # the OpenRouter model id, or "scripted"
    prompt_version: Literal["v1", "v2"]
    record: DecisionRecord
    expected: ExpectedOutcome
    check: CheckKind
    decision_ok: bool            # code check: record["decision"] == expected_decision
    trigger_ok: bool             # code check: right outcome by the WRONG trigger is NOT a pass
    passed: bool                 # decision_ok AND trigger_ok (AND the judgement, where used)
    notes: str


# ─────────────────────────────────────────────────────────────────────────────
# The seam between the loop and the harness. ONE function, and it is the only thing
# the harness is allowed to know about the agent.
# ─────────────────────────────────────────────────────────────────────────────

def run_case(case_id: str, *, prompt_version: str = "v2") -> DecisionRecord:
    """Run the agent once, start to finish, on one case. Isolated: no state from a previous run.

    WHAT          One complete execution of the ReAct loop on one claim.
    INPUT         case_id str — a claim_id present in data_A/claims.json.
                  prompt_version "v1" | "v2" — held fixed across a model battery.
    RETURNS       exactly one DecisionRecord, with `usage` populated on every path,
                  including the paths that never reach the gated action.
    FAILS WHEN    case_id resolves to no claim; a cap fires (record is still returned,
                  with usage["cap_fired"] set — the stop must be LOUD, never a silent empty answer).
    IRREVERSIBLE? No. The one irreversible step is inside, behind the autonomy gate.

    Implemented by: Goncalo Miranda / ZHENG YONGJIE (D1). See PLAN.md §2.
    """
    raise NotImplementedError("D1 — the loop. See PLAN.md §2.")


# ─────────────────────────────────────────────────────────────────────────────
# The vendor seam. Exactly ONE function in this repository knows a vendor exists.
# Switching model is a string. This is the Class 4 pattern.
# ─────────────────────────────────────────────────────────────────────────────

Backend = Literal["scripted", "openrouter"]

BACKEND: Backend = "scripted"       # <- the DEFAULT, and it must stay the default
MODEL: str = "openai/gpt-4o-mini"
BASE_URL: str = "https://openrouter.ai/api/v1"


def complete(messages: List[Dict[str, str]], *, model: str = MODEL) -> Dict:
    """The only function that knows a vendor exists.

    When BACKEND == "scripted" it replays deterministic canned responses: no network, no key,
    same answer every time. A marker clones the repository and reproduces every number at zero
    cost. If the harness does not run this way, Technical Execution is capped.

    Implemented by: JIN CHENG / NIU TONG (D5a). See PLAN.md §2.
    """
    raise NotImplementedError("D5(a) — the scripted backend. See PLAN.md §2.")
