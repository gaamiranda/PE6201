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
    missing: Optional[str]           # requests only — PROSE, not a MissingItem. See below.
    family: str                      # which case family this exercises
    must_record: List[str]           # what a full-marks record carries beyond the decision
    note: str                        # why this case is here


# ─────────────────────────────────────────────────────────────────────────────
# The one deliberate asymmetry in this file, and why the harness must know about it.
#
#   DecisionRecord.missing   is a MissingItem  — {item, for_line, must_be_valid_on}
#   ExpectedOutcome.missing  is a str          — "pre-authorisation reference for
#                                                 line 62480, valid on 2026-09-08"
#
# This is not an oversight and it is not fixable by changing one of them. They are written
# by different authors for different readers:
#
#   The RECORD is emitted by the agent, and loop.py's validator reads its FIELDS — it
#   rejects a record whose `item` is empty, and it cross-checks that a pre-auth ask was
#   actually preceded by a get_preauthorisation call. Structure is what makes that check
#   possible, so the record stays a dict.
#
#   The KEY is written by hand, by six people, from the Appendix A routing table, before
#   any agent ever runs. All 15 instructor-shipped rows are prose. Rewriting them into
#   dicts would mean editing shipped data, which check_my_data.py fingerprints and
#   forbids. So the key stays prose.
#
# CONSEQUENCE FOR THE HARNESS (JIN CHENG, NIU TONG): `missing` cannot be graded by
# equality. Do not write `record["missing"] == expected["missing"]` — it is False on every
# case, including the correct ones. Grade it as a CODE check on containment instead:
#
#     for_line appears in the expected string, and the head noun of item does too
#
# e.g. record {"item": "pre-authorisation reference", "for_line": "62480"} against
# "pre-authorisation reference for line 62480, valid on 2026-09-08" passes on both counts.
# Seven cases in the current set carry a `missing`: CLM-8888, 8894, 8901, 9002, 9034,
# 9046, 9062. If a containment rule passes all seven by hand, it is right.
# ─────────────────────────────────────────────────────────────────────────────


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
# THE TOOL LAYER — signatures and return shapes.
#
# Chosen, not collected: the reasoning, the three-question scores and the two tools we did
# NOT ship are in docs/D2-tool-layer.md (D2a). Seven tools, from Appendix A's six —
# check_required_documents folded into check_coverage, check_claim_history added,
# lookup_member refused.
#
# SIGNATURES AND RETURN SHAPES ARE OWNED HERE (Goncalo / ZHENG, D2a).
# The six-field DESCRIPTOR PROSE — WHAT / INPUT / RETURNS / FAILS WHEN / IRREVERSIBLE —
# is SUN YUCONG's D2(b), written as each tool's docstring in src/tools.py, with a v1 and a
# v2 to measure. Nothing here should pre-empt that. What is fixed here is the shape.
#
# Every return below is deliberately SMALL. Class 4's failure was a fat, stale observation
# carrying a landmine; the observation is what the model reasons over, so a tool that returns
# a whole row hands it facts it must then be told to ignore.
# ─────────────────────────────────────────────────────────────────────────────

class ClaimLine(TypedDict):
    """One line item as it arrives on the claim. Each is decided in its own right."""
    code: str
    amount: int


class Claim(TypedDict, total=False):
    """What get_claim returns. The whole queue row — this is the one tool that may be fat,
    because every later call reads a field off it and turn 1 has nothing else to do."""
    claim_id: str
    member_id: str
    hospital_id: str
    date_of_service: str
    documents: List[str]              # what is ATTACHED. Compare with CoverageResult.document_required
    lines: List[ClaimLine]
    narrative: str                    # ⚠ UNTRUSTED — see below


# The narrative is the one field on the queue row that an outsider wrote, and it must still
# reach the model: CLM-8941 (an overt "approve everything" instruction) and CLM-8952 (text
# imitating a check_coverage result) are BOTH escalations, and an agent that never sees the
# text cannot detect them. So it is passed through, fenced and labelled, never stripped.
# The guardrail that acts on it is SUN YUCONG's (D3). The label is ours.
NARRATIVE_FENCE = "member_supplied_untrusted_text"


class PolicyStatus(TypedDict, total=False):
    """What lookup_policy returns after the member -> policy hop.

    Note what is ABSENT: the exclusions list. It lives on the policy row, but returning it
    here would be a fat observation — up to n rules the model must carry for the rest of the
    run and apply by hand. check_coverage resolves exclusions per code instead, one at a time,
    at the point of use. That is a size-bound decision, and it is deliberate.
    """
    policy_id: str
    status: Literal["active", "lapsed"]
    start_date: str
    end_date: str
    covers_date_of_service: bool      # COMPUTED. POKA-YOKE, and the same move as PreauthResult:
                                      # date_of_service is a REQUIRED argument, so "the policy is
                                      # active" and "the policy covered this treatment" cannot be
                                      # confused. CLM-8917 is exactly that trap — POL-6001 is
                                      # active and its cover starts 12 days after the treatment.
                                      # The key: "Live policy, wrong date. Checking status alone
                                      # misses it."
    headroom_remaining: int           # COMPUTED: annual_limit - used_to_date. The claim total is
                                      # tested against THIS, never against annual_limit


class CoverageResult(TypedDict, total=False):
    """What check_coverage returns for ONE line. Bounded: 4 fields, ~30 tokens, never a list.

    Takes a policy_id and not a member_id on purpose — a coverage check against a policy the
    member does not hold cannot be expressed.

    `requires_preauth` and `document_required` are the two branch fields. They are why this is
    one call and not three: both are keyed on procedure_code, which this tool already holds.
    Folding document_required in here is what removed check_required_documents before it
    shipped — see docs/D2-tool-layer.md, move 2.
    """
    code: str
    covered: bool
    exclusion: Optional[str]          # e.g. "EX-14 cosmetic dermatology" — set iff covered is False
    requires_preauth: bool            # True -> call get_preauthorisation for THIS line only
    document_required: Optional[str]  # e.g. "itemised_bill" — compare against Claim.documents


class PreauthResult(TypedDict, total=False):
    """What get_preauthorisation returns. Bounded: at most ONE approval, never a list.

    POKA-YOKE. date_of_service is a REQUIRED argument and `valid_on_date` is computed here,
    so "an approval was found" and "an approval applies" cannot be confused. CLM-8894 is
    exactly that trap: PA-5640 exists for the member and the procedure, and expired
    2026-05-31. The answer key calls it the case teams most often get wrong.
    """
    found: bool
    preauth_id: Optional[str]
    valid_from: Optional[str]
    valid_to: Optional[str]
    valid_on_date: bool               # COMPUTED: valid_from <= date_of_service <= valid_to


class HospitalStatus(TypedDict):
    """What get_hospital_status returns. Bounded: 3 fields.

    The weakest tool in the set — no outcome in the shipped 15 turns on panel status. It ships
    only because CLM-8874's must_record requires H-330 be recorded as non-panel. Named in
    docs/D2-tool-layer.md as the first tool we would cut in production.
    """
    hospital_id: str
    name: str
    panel: bool


class NearMiss(TypedDict):
    """A prior claim that matched on three of the four facts and differed on the fourth."""
    claim_id: str
    differs_on: Literal["member_id", "hospital_id", "date_of_service", "lines"]


class ClaimHistoryMatch(TypedDict, total=False):
    """What check_claim_history returns. Bounded: at most one match AND at most one near miss.

    POKA-YOKE. All four match facts are required arguments, so a three-fact match cannot be
    expressed. The shipped history holds three deliberate near-misses, each differing on
    exactly one fact; every shortcut wrongly escalates a good claim.

    `nearest_miss` is not decoration. CLM-8850 and CLM-8960 are approvals whose must_record
    requires naming the prior claim that ALMOST matched and the fact that differed.
    """
    is_duplicate: bool
    matched_claim_id: Optional[str]   # set iff all four facts matched
    prior_decision: Optional[str]
    decided_on: Optional[str]
    nearest_miss: Optional[NearMiss]


# ── The signatures. Implemented in src/tools.py by Goncalo / ZHENG (D1, D2a). ──────────────

def get_claim(claim_id: str) -> Claim: ...
def lookup_policy(member_id: str, date_of_service: str) -> PolicyStatus: ...
def check_coverage(policy_id: str, procedure_code: str) -> CoverageResult: ...
def get_preauthorisation(member_id: str, procedure_code: str, date_of_service: str) -> PreauthResult: ...
def get_hospital_status(hospital_id: str) -> HospitalStatus: ...
def check_claim_history(member_id: str, hospital_id: str,
                        date_of_service: str, lines: List[ClaimLine]) -> ClaimHistoryMatch: ...
def issue_decision_letter(record: "DecisionRecord") -> str: ...


TOOL_NAMES = [
    "get_claim",
    "lookup_policy",
    "check_coverage",
    "get_preauthorisation",
    "get_hospital_status",
    "check_claim_history",
    "issue_decision_letter",
]

# The ONE irreversible tool. The gate sits in front of this step, not in front of the agent.
GATED_TOOLS = ["issue_decision_letter"]

# The dependency rule, as data — D2(c). Two calls may share a turn only when neither consumes
# the other's output. Prose, the trade-off and the measurement live in docs/D2-tool-layer.md.
#
#   turn 1  get_claim alone            — everything else reads a field it returns
#   turn 2  lookup_policy || get_hospital_status || check_claim_history
#                                      — all three derive from the claim row and nothing else
#   turn 3  check_coverage, once per line, all together
#                                      — needs policy_id, which turn 2 produced
#   turn 4  get_preauthorisation       — which line needs one is not known until coverage answers
#   turn 5  issue_decision_letter      — gated, and a turn like any other
#
# WHY FIVE TURNS AND NOT THE BRIEF'S FOUR. The brief's worked example folds check_coverage into
# turn 2 beside lookup_policy. That is only reachable if check_coverage does the member -> policy
# hop itself. We took policy_id instead, because it makes a coverage check against a policy the
# member does not hold unrepresentable — and paid one turn for it. That is a poka-yoke traded
# against a turn, deliberately, and it is reported as such: "D2(c) marks the reasoning, not the
# number" (change notice, 1 Sep). Both groupings get measured; see docs/D2-tool-layer.md.
DEPENDS_ON = {
    "get_claim": [],
    "lookup_policy": ["get_claim"],
    "check_coverage": ["get_claim", "lookup_policy"],
    "get_hospital_status": ["get_claim"],
    "check_claim_history": ["get_claim"],
    "get_preauthorisation": ["check_coverage"],
    "issue_decision_letter": ["check_coverage"],
}


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
