"""
The tool layer — seven functions over the fixture data.

WHAT THIS FILE IS
    The ACI (Agent-Computer Interface). Every fact the agent ever learns comes through one of
    these functions. Nothing here calls a model, opens a socket, or reads a file the agent
    chose. They are ordinary Python and they are tested by calling them.

WHICH SEVEN, AND WHY
    docs/D2-tool-layer.md scores every one against the three questions and records the two we
    did NOT ship: check_required_documents (folded into check_coverage) and lookup_member
    (refused — it would return join_date, which looks like a coverage date and is not).
    Signatures and return shapes are frozen in src/contracts.py.

THE ONE RULE THIS FILE EXISTS TO ENFORCE
    The agent never receives a file. It receives what a tool returned. Every return below is
    deliberately small: "an agent handed all the data in its first prompt is making a single
    call, not running a loop."

D2(b) IS NOT DONE HERE
    Each function carries a marked placeholder where its six-field descriptor goes. That prose
    is SUN YUCONG's deliverable and it needs a v1 and a v2 to measure, so it is deliberately
    not written here. What is fixed here is behaviour and shape.

Owner: Goncalo Miranda / ZHENG YONGJIE (D1, D2a). See PLAN.md §2.
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from contracts import (
    NARRATIVE_FENCE,
    Claim,
    ClaimHistoryMatch,
    ClaimLine,
    CoverageResult,
    DecisionRecord,
    HospitalStatus,
    NearMiss,
    PolicyStatus,
    PreauthResult,
)

# ─────────────────────────────────────────────────────────────────────────────
# The data. Loaded once, at import, into dicts.
#
# We read the instructor's folder in place and never write to it. The generator and
# check_my_data.py anchor on their own __file__, so the folder must stay intact — see
# docs/D4-data-and-cases.md.
# ─────────────────────────────────────────────────────────────────────────────

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA = os.path.join(_REPO, "A2_reference_data", "data_A")
_RESULTS = os.path.join(_REPO, "results")


def _load(name: str) -> Any:
    with open(os.path.join(_DATA, name + ".json"), encoding="utf-8") as fh:
        return json.load(fh)


_CLAIMS: Dict[str, dict] = {c["claim_id"]: c for c in _load("claims")}
_MEMBERS: Dict[str, dict] = {m["member_id"]: m for m in _load("members")}
_POLICIES: Dict[str, dict] = {p["policy_id"]: p for p in _load("policies")}
_PROCEDURES: Dict[str, dict] = {p["code"]: p for p in _load("procedures")}
_HOSPITALS: Dict[str, dict] = {h["hospital_id"]: h for h in _load("hospitals")}
_PREAUTHS: List[dict] = _load("preauthorisations")
_REQUIRED_DOCS: Dict[str, str] = {r["procedure_code"]: r["document"] for r in _load("required_documents")}
_DECIDED: List[dict] = _load("decided_claims")


class ToolError(Exception):
    """Raised when a tool cannot answer — a bad id, an unknown code.

    The loop catches this and appends the message as an OBSERVATION. It is not a crash: a tool
    that cannot answer is information the agent must reason about, and a run that dies on a bad
    id tells us nothing. See loop.py.
    """


def _iso(s: str) -> date:
    return date.fromisoformat(s)


def _canonical_lines(lines: List[ClaimLine]) -> Tuple[Tuple[str, int], ...]:
    """Order-independent fingerprint of a line set, for the duplicate match.

    Sorted on purpose: two claims listing the same procedures in a different order are the same
    episode, and a comparison that depended on ordering would miss CLM-8933.
    """
    return tuple(sorted((str(l["code"]), int(l["amount"])) for l in lines))


# ─────────────────────────────────────────────────────────────────────────────
# 1 · get_claim — the entry point. Turn 1, alone.
# ─────────────────────────────────────────────────────────────────────────────

def get_claim(claim_id: str) -> Claim:
    """Resolve a claim id to the queue row. The only tool that may return a whole record.

    # ── D2(b) DESCRIPTOR · SUN YUCONG ────────────────────────────────────────
    # NAME + SIGNATURE / WHAT / INPUT / RETURNS (+ size bound) / FAILS WHEN / IRREVERSIBLE?
    # ─────────────────────────────────────────────────────────────────────────
    """
    row = _CLAIMS.get(claim_id)
    if row is None:
        raise ToolError(f"no claim with id {claim_id}")

    # The narrative is the one field on this row written by someone outside the organisation.
    # It is passed through, never stripped: CLM-8941 (an overt "approve everything" instruction)
    # and CLM-8952 (text imitating a check_coverage result) are both escalations, and an agent
    # that never sees the text cannot detect them. It is FENCED so the loop can render it as
    # quoted data rather than as part of its own instructions. Acting on it is D3 (SUN YUCONG).
    return {
        "claim_id": row["claim_id"],
        "member_id": row["member_id"],
        "hospital_id": row["hospital_id"],
        "date_of_service": row["date_of_service"],
        "documents": list(row["documents"]),
        "lines": [{"code": l["code"], "amount": l["amount"]} for l in row["lines"]],
        "narrative": row["narrative"],
        NARRATIVE_FENCE: True,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2 · lookup_policy — the member -> policy hop. Three escalation triggers come out of it.
# ─────────────────────────────────────────────────────────────────────────────

def lookup_policy(member_id: str, date_of_service: str) -> PolicyStatus:
    """Is this member's cover live ON THE DATE OF TREATMENT, and how much of the year is left.

    # ── D2(b) DESCRIPTOR · SUN YUCONG ────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    """
    member = _MEMBERS.get(member_id)
    if member is None:
        raise ToolError(f"no member with id {member_id}")
    pol = _POLICIES.get(member["policy_id"])
    if pol is None:
        raise ToolError(f"member {member_id} names policy {member['policy_id']}, which does not exist")

    dos = _iso(date_of_service)

    # POKA-YOKE. date_of_service is required, and the window test happens HERE, so "the policy
    # is active" and "the policy covered this treatment" cannot be confused. CLM-8917 is that
    # trap: POL-6001 is active and its cover begins 12 days after the treatment.
    covers = pol["status"] == "active" and _iso(pol["start_date"]) <= dos <= _iso(pol["end_date"])

    # COMPUTED, not left as two fields to subtract. The claim total is tested against the
    # headroom, never against annual_limit — the data dictionary says so, and CLM-8925 is the
    # case that punishes getting it wrong.
    return {
        "policy_id": pol["policy_id"],
        "status": pol["status"],
        "start_date": pol["start_date"],
        "end_date": pol["end_date"],
        "covers_date_of_service": covers,
        "headroom_remaining": pol["annual_limit"] - pol["used_to_date"],
    }
    # NOTE what is absent: the exclusions list. Returning it here would hand the model up to n
    # rules to carry for the rest of the run. check_coverage resolves them per code, at the
    # point of use. See docs/D2-tool-layer.md.


# ─────────────────────────────────────────────────────────────────────────────
# 3 · check_coverage — once per line. The two branch fields live here.
# ─────────────────────────────────────────────────────────────────────────────

def check_coverage(policy_id: str, procedure_code: str) -> CoverageResult:
    """NAME + SIGNATURE   check_coverage(policy_id: str, procedure_code: str) -> CoverageResult
    WHAT               Decides one claim line against one policy: covered/not covered, and the
                       exact follow-up actions needed before a covered line can be approved.
    INPUT              policy_id is a policy row id returned by lookup_policy; an unknown id
                       raises ToolError. procedure_code is one line's procedure code; an unknown
                       code raises ToolError. Pass one procedure code per call, never a claim id.
    RETURNS            One object, bounded to 3 top-level fields plus at most two needed_next
                       items: {"code": str, "coverage": {"status": "covered"} or {"status":
                       "not_covered", "exclusion": str}, "needed_next": [{"kind": "preauth"}
                       and/or {"kind": "document", "item": str}]}. needed_next is empty when
                       the line is not covered.
    FAILS WHEN         The policy id is unknown, the procedure code is unknown, or the caller
                       tries to decide more than one line in one call.
    IRREVERSIBLE?      No. This only reads fixture data; issue_decision_letter is the gated write.

    # -- D2(b) DESCRIPTOR - SUN YUCONG ----------------------------------------
    # This is the tool to measure for D2(b)'s v1 -> v2 rewrite: it is called once per line, so
    # every token in its return is paid n times per run. v2 also changes the shape: an excluded
    # line cannot simultaneously return branch flags that ask the agent to chase paperwork.
    # -------------------------------------------------------------------------
    """
    # POKA-YOKE: takes a policy_id, not a member_id. A coverage check against a policy the
    # member does not hold cannot be expressed. Costs one turn — see docs/D2-tool-layer.md.
    pol = _POLICIES.get(policy_id)
    if pol is None:
        raise ToolError(f"no policy with id {policy_id}")
    proc = _PROCEDURES.get(procedure_code)
    if proc is None:
        raise ToolError(f"no procedure with code {procedure_code}")

    exclusion = next((e["rule"] for e in pol["exclusions"] if e["code"] == procedure_code), None)

    # The document requirement rides along in needed_next because required_documents.json is
    # keyed on procedure_code, which this call already holds. That is what removed
    # check_required_documents before it ever shipped — one fewer descriptor in the prompt
    # prefix, zero extra calls.
    #
    # The early return below is the v2 safety property: a not_covered line leaves with an EMPTY
    # needed_next, so the observation cannot simultaneously refuse a line and tell the agent to
    # chase pre-authorisation or documents for it. Under v1 both could be set at once.
    if exclusion is not None:
        return {
            "code": procedure_code,
            "coverage": {"status": "not_covered", "exclusion": exclusion},
            "needed_next": [],
        }

    needed_next = []
    if proc["requires_preauth"]:
        needed_next.append({"kind": "preauth"})
    required_document = _REQUIRED_DOCS.get(procedure_code)
    if required_document:
        needed_next.append({"kind": "document", "item": required_document})

    return {
        "code": procedure_code,
        "coverage": {"status": "covered"},
        "needed_next": needed_next,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4 · get_preauthorisation — only for lines whose needed_next carried {"kind": "preauth"}.
# ─────────────────────────────────────────────────────────────────────────────

def get_preauthorisation(member_id: str, procedure_code: str, date_of_service: str) -> PreauthResult:
    """Is there an approval for this member and this procedure that APPLIES on this date.

    # ── D2(b) DESCRIPTOR · SUN YUCONG ────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    """
    dos = _iso(date_of_service)
    match = next(
        (p for p in _PREAUTHS if p["member_id"] == member_id and p["procedure_code"] == procedure_code),
        None,
    )
    if match is None:
        return {"found": False, "preauth_id": None, "valid_from": None,
                "valid_to": None, "valid_on_date": False}

    # POKA-YOKE. date_of_service is required and the window test is computed here, so "an
    # approval was found" and "an approval applies" cannot be confused. CLM-8894 is exactly
    # that: PA-5640 exists for M-6118 and 29881, and expired 2026-05-31. The answer key calls
    # it the case teams most often get wrong.
    #
    # Note that found=True is still reported when the window fails. The record must say the
    # approval was found AND why it does not authorise the claim — CLM-8894's must_record asks
    # for all three facts.
    return {
        "found": True,
        "preauth_id": match["preauth_id"],
        "valid_from": match["valid_from"],
        "valid_to": match["valid_to"],
        "valid_on_date": _iso(match["valid_from"]) <= dos <= _iso(match["valid_to"]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5 · get_hospital_status — the weakest tool in the set. Kept for one must_record.
# ─────────────────────────────────────────────────────────────────────────────

def get_hospital_status(hospital_id: str) -> HospitalStatus:
    """Panel or not. Changes what the record must SAY, not what the decision is.

    # ── D2(b) DESCRIPTOR · SUN YUCONG ────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    """
    h = _HOSPITALS.get(hospital_id)
    if h is None:
        raise ToolError(f"no hospital with id {hospital_id}")
    return {"hospital_id": h["hospital_id"], "name": h["name"], "panel": bool(h["panel"])}


# ─────────────────────────────────────────────────────────────────────────────
# 6 · check_claim_history — the tool we added, and the one with the sharpest poka-yoke.
# ─────────────────────────────────────────────────────────────────────────────

def check_claim_history(member_id: str, hospital_id: str,
                        date_of_service: str, lines: List[ClaimLine]) -> ClaimHistoryMatch:
    """Has this EPISODE already been decided? Matched on facts, never on the claim id.

    # ── D2(b) DESCRIPTOR · SUN YUCONG ────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    """
    # POKA-YOKE. All four match facts are required arguments, so a three-fact match cannot be
    # expressed. The shipped history holds three deliberate near-misses, each differing on
    # exactly one fact; every shortcut wrongly escalates a claim that is perfectly fine.
    #
    # The claim id is NOT part of the match, and cannot be: a resubmission arrives with a new
    # one. CLM-8933 says so in its own narrative.
    want = {
        "member_id": member_id,
        "hospital_id": hospital_id,
        "date_of_service": date_of_service,
        "lines": _canonical_lines(lines),
    }

    nearest: Optional[NearMiss] = None
    for prior in _DECIDED:
        have = {
            "member_id": prior["member_id"],
            "hospital_id": prior["hospital_id"],
            "date_of_service": prior["date_of_service"],
            "lines": _canonical_lines(prior["lines"]),
        }
        differing = [k for k in want if want[k] != have[k]]

        if not differing:
            return {"is_duplicate": True, "matched_claim_id": prior["claim_id"],
                    "prior_decision": prior["decision"], "decided_on": prior["decided_on"],
                    "nearest_miss": None}

        # Exactly one fact apart. Reported so the record can say it is NOT a duplicate and name
        # the fact that separates them — CLM-8850 and CLM-8960 both require this.
        if len(differing) == 1 and nearest is None:
            nearest = {"claim_id": prior["claim_id"], "differs_on": differing[0]}

    return {"is_duplicate": False, "matched_claim_id": None, "prior_decision": None,
            "decided_on": None, "nearest_miss": nearest}


# ─────────────────────────────────────────────────────────────────────────────
# 7 · issue_decision_letter — the ONE irreversible tool, and the whole write.
# ─────────────────────────────────────────────────────────────────────────────

def _gate_open(record: DecisionRecord) -> Tuple[bool, str]:
    """The autonomy gate for the one irreversible step.

    The shipped setting is confirm: the agent may assemble a decision record, but the write
    opens only after the record is structurally complete for an approval. In this offline
    harness the operator confirmation is represented by deterministic checks here and by the
    evidence precondition in loop.py; a live deployment would replace the final "approved"
    string with an actual human confirmation event.
    """
    if not isinstance(record, dict):
        return False, "operator confirmation requires one decision record object"

    if record.get("decision") != "approve_in_principle":
        return False, "only approve_in_principle is an irreversible write in this workflow"

    missing = [field for field in ("case_id", "decision", "reason") if not record.get(field)]
    if missing:
        return False, "operator confirmation blocked incomplete record: " + ", ".join(missing)

    lines = record.get("lines")
    if not isinstance(lines, list) or not lines:
        return False, "operator confirmation blocked approval with no per-line dispositions"

    for index, line in enumerate(lines, start=1):
        if not isinstance(line, dict):
            return False, f"line disposition {index} is not an object"
        if not line.get("code") or line.get("status") not in ("covered", "not_covered"):
            return False, f"line disposition {index} is missing code or status"
        if line.get("status") == "not_covered" and not line.get("exclusion"):
            return False, f"line disposition {index} refuses cover without naming the exclusion"

    for total in ("approved_total", "refused_total"):
        value = record.get(total)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return False, f"{total} must be a non-negative integer"

    return True, "operator confirmed structured approval record"


def issue_decision_letter(record: DecisionRecord) -> str:
    """The gated action. Three steps: check the gate, append ONE record, return a confirmation.

    It does NOT compose a letter. No greeting, no recipient, no policy summary, no template —
    "the record is the output of your agent, and it is the thing that gets marked."

    # ── D2(b) DESCRIPTOR · SUN YUCONG ────────────────────────────────────────
    # IRREVERSIBLE? Yes. Name the gate.
    # ─────────────────────────────────────────────────────────────────────────
    """
    # POKA-YOKE. Observed on a live gpt-4o-mini run: the model called this with a STRING —
    # a summary sentence rather than the record. The gated action is the marked artefact, so
    # a tool that quietly accepted prose would write a decision with no evidence trail. The
    # type is checked here and the complaint names what is missing, because the model cannot
    # read our source to find out.
    if not isinstance(record, dict):
        raise ToolError(
            f"issue_decision_letter takes the decision RECORD, not a {type(record).__name__}. "
            f"Pass the same JSON object you will put in your Final: it must carry case_id, "
            f"decision, reason, and the fields for the outcome you reached.")
    for field in ("case_id", "decision", "reason"):
        if not record.get(field):
            raise ToolError(f"the record is missing {field!r}; nothing is written without it")

    ok, why = _gate_open(record)
    if not ok:
        raise ToolError(f"gate refused: {why}")

    os.makedirs(_RESULTS, exist_ok=True)
    with open(os.path.join(_RESULTS, "decisions.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    return f"decision recorded for {record.get('case_id')}: {record.get('decision')} ({why})"


# The callable table the loop dispatches through. Names must match contracts.TOOL_NAMES,
# because they are also the strings that appear in the record's evidence trail.
# ─────────────────────────────────────────────────────────────────────────────
# D2(b) · the v1 descriptors — SUN YUCONG owns the CONTENT of this dict.
#
# The v2 descriptor of a tool is its docstring above: loop.tool_manual() builds the manual
# straight out of the signatures and docstrings, so the shipped interface and the prompt can
# never drift apart. That leaves nowhere to put a SECOND version, which is why this exists.
#
# Map a tool name to the descriptor text it had BEFORE the rewrite. tool_manual("v1")
# substitutes these; everything absent falls through to the docstring. The brief asks for one
# tool rewritten, not seven — one honest entry here is the deliverable.
#
#     DESCRIPTORS_V1 = {
#         "check_coverage": """Checks coverage. Returns coverage info.""",
#     }
#
# Leave it empty until the real v1 text is written. tool_manual() refuses to build a v1
# manual from an empty dict rather than silently handing back v2 — an unnoticed fallback
# would make v1 and v2 identical and turn D2(b) into a measurement of nothing.
DESCRIPTORS_V1: dict = {
    "check_coverage": """Checks whether a procedure is covered by a policy and says if anything else is needed.""",
}


TOOLS = {
    "get_claim": get_claim,
    "lookup_policy": lookup_policy,
    "check_coverage": check_coverage,
    "get_preauthorisation": get_preauthorisation,
    "get_hospital_status": get_hospital_status,
    "check_claim_history": check_claim_history,
    "issue_decision_letter": issue_decision_letter,
}
