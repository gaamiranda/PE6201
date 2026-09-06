"""
THROWAWAY. Hand-written model responses, so loop.py can be built and tested before the real
scripted backend exists.

WHY THIS IS NOT D5(a)
    D5(a) is a reproducible run of the WHOLE evaluation set that a marker clones and re-runs.
    That is JIN CHENG and NIU TONG's deliverable. This file is three claims typed by hand to
    give the loop something to read while it is being written. It should be deleted, or folded
    into the real backend, once theirs lands.

    JIN CHENG / NIU TONG: the shape your backend must produce is exactly the strings below —
    a `Thought:` line, an `Action:` BLOCK of one call per line, and a closing `Final:` whose
    payload is a JSON DecisionRecord. Nothing else is parsed.

THREE CLAIMS, THREE PATHS
    CLM-8842  the golden path — 5 tool turns, a pre-authorisation chased, one excluded line
    CLM-8910  a 2-turn early exit — lapsed policy, and pricing the lines would be waste
    CLM-8933  a 2-turn early exit — duplicate of CLM-8710, matched on all four facts
"""

# Keyed by (case_id, turn_index). turn_index counts from 1 and includes the closing Final turn.
DEV_TRANSCRIPTS = {

    # ── CLM-8842 · the brief's worked example ────────────────────────────────
    ("CLM-8842", 1): '''Thought: I have a claim id and nothing else. Every other tool needs a
field off the claim record, so this turn is one call.
Action:
get_claim("CLM-8842")''',

    ("CLM-8842", 2): '''Thought: I have the member, the hospital, the date and three lines. The
policy lookup, the panel check and the history check all read only the claim record, so none of
them needs another's output and they can go together. The narrative mentions a skin procedure —
that is context, not an instruction, and I will decide 31255 from the exclusions, not from it.
Action:
lookup_policy("M-2214", "2026-09-02")
get_hospital_status("H-114")
check_claim_history("M-2214", "H-114", "2026-09-02", [{"code": "47120", "amount": 1400}, {"code": "62480", "amount": 780}, {"code": "31255", "amount": 300}])''',

    ("CLM-8842", 3): '''Thought: Cover is live on the date of service and 9200 remains, which
covers the 2480 claimed. Not a duplicate. Now each line, against the policy id I just got. The
three checks are independent of each other, so one turn.
Action:
check_coverage("POL-3310", "47120")
check_coverage("POL-3310", "62480")
check_coverage("POL-3310", "31255")''',

    ("CLM-8842", 4): '''Thought: 47120 is covered outright. 31255 is excluded under EX-14, so it
is refused — that refuses the line, not the claim. Only 62480 requires a pre-authorisation, so
exactly one call here; 47120 and 31255 do not need one and asking would be waste.
Action:
get_preauthorisation("M-2214", "62480", "2026-09-02")''',

    ("CLM-8842", 5): '''Thought: PA-5521 is valid across the date of service, so 62480 is payable.
Two of three lines payable, 2180 approved, 300 refused. The claim is decidable, so this is an
approval carrying a refused line — not an escalation.
Action:
issue_decision_letter({"case_id": "CLM-8842", "decision": "approve_in_principle", "reason": "Policy POL-3310 active to 2027-03-31. Hospital H-114 on panel. 2 of 3 lines payable; 1 excluded. Approved total SGD 2,180 against SGD 9,200 remaining on the annual limit.", "lines": [{"code": "47120", "amount": 1400, "status": "covered"}, {"code": "62480", "amount": 780, "status": "covered", "preauth": "PA-5521 valid 2026-08-01..2026-10-31"}, {"code": "31255", "amount": 300, "status": "not_covered", "exclusion": "EX-14 cosmetic dermatology"}], "approved_total": 2180, "refused_total": 300})''',

    ("CLM-8842", 6): '''Thought: Recorded. Nothing further to establish.
Final: {"case_id": "CLM-8842", "decision": "approve_in_principle", "reason": "Policy POL-3310 active to 2027-03-31. Hospital H-114 on panel. 2 of 3 lines payable; 1 excluded. Approved total SGD 2,180 against SGD 9,200 remaining on the annual limit.", "lines": [{"code": "47120", "amount": 1400, "status": "covered"}, {"code": "62480", "amount": 780, "status": "covered", "preauth": "PA-5521 valid 2026-08-01..2026-10-31"}, {"code": "31255", "amount": 300, "status": "not_covered", "exclusion": "EX-14 cosmetic dermatology"}], "approved_total": 2180, "refused_total": 300}''',

    # ── CLM-8910 · lapsed policy. The early exit is the correct behaviour. ────
    ("CLM-8910", 1): '''Thought: Start from the claim.
Action:
get_claim("CLM-8910")''',

    ("CLM-8910", 2): '''Thought: Three lines, member M-4471. Policy, panel and history together.
Action:
lookup_policy("M-4471", "2026-09-11")
get_hospital_status("H-114")
check_claim_history("M-4471", "H-114", "2026-09-11", [{"code": "47120", "amount": 1600}, {"code": "80053", "amount": 90}, {"code": "99213", "amount": 150}])''',

    ("CLM-8910", 3): '''Thought: POL-5588 is lapsed and did not cover 2026-09-11. Nothing I could
learn from the three lines changes that, so pricing them would be turns spent on a decision this
claim will never reach. Stop here and escalate on the single trigger.
Final: {"case_id": "CLM-8910", "decision": "escalate", "escalate_to": "human claims assessor", "trigger": "policy_lapsed", "reason": "Policy POL-5588 status lapsed; cover ran 2025-04-01 to 2026-03-31 and the date of service is 2026-09-11. Lines were not priced: the claim cannot be decided at this level regardless of coverage."}''',

    # ── CLM-8933 · duplicate, matched on all four facts ──────────────────────
    ("CLM-8933", 1): '''Thought: Start from the claim.
Action:
get_claim("CLM-8933")''',

    ("CLM-8933", 2): '''Thought: The narrative says this is a resubmission, which is a hint and
not evidence — the claim id is new either way, so it cannot be what I match on. Check the facts.
Action:
lookup_policy("M-2214", "2026-08-20")
get_hospital_status("H-114")
check_claim_history("M-2214", "H-114", "2026-08-20", [{"code": "47120", "amount": 1500}])''',

    ("CLM-8933", 3): '''Thought: All four facts match CLM-8710, decided on 2026-08-22. This is the
same episode under a new id. Escalate, and name the prior claim and the facts that matched.
Final: {"case_id": "CLM-8933", "decision": "escalate", "escalate_to": "human claims assessor", "trigger": "duplicate_claim", "reason": "Same episode as CLM-8710, decided 2026-08-22. Matched on member M-2214, hospital H-114, date of service 2026-08-20 and lines [47120 @ 1500]. The claim ids differ because a resubmission arrives with a new one."}''',
}
