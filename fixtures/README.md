# fixtures — local data the tools read

Small local files standing in for the systems of record. **No live systems and no real accounts** —
nothing the agent touches may be somebody's actual record.

> **Shipped midday Wednesday 2 September** on NTULearn: the reference data for both problems, the
> scripts that generate it, a **data guide** (what each file contains, the shape of every field, and
> how the files connect), and **`check_my_data.py`**.

## The one rule for extending the data

> **Add new rows with new ids. Never edit or delete a row the instructor shipped.**

Everything else follows from it. A marker re-runs our harness against the original records, so an
edited row breaks reproduction. Run **`check_my_data.py`** over your additions — it tells you if you
have referred to something that does not exist, changed a shipped record, or duplicated an id.

Commit whatever generates or holds our additions, so the data set is reproducible rather than a
mystery. The team self-appraisal now carries a **fixture-integrity declaration** confirming we added
rather than edited.

## Guide to size

**30–50 primary records** (claims / referrals) plus the supporting rows they reference. Enough to
make the evaluation set meaningful and no more.

## The thing that silently breaks everything

The files connect to one another, and that is how the agent gets from one fact to the next. A claim
carries a `member_id`; the members file is keyed by that same `member_id`, and following it is what
lets `lookup_policy` find the policy that covers them. **Invent a claim whose `member_id` matches
nobody and the agent will look perfectly sound and return nothing.** `check_my_data.py` exists to
catch exactly this.

Extending the fixtures deliberately to create a negative case is good practice and worth mentioning
in the report.

## Answer key

`expected_outcomes_A.json` / `_B.json` give the outcome the Appendix A **routing rule** requires and
the single trigger that produces it. That is the ground truth for D4, and the shape our own labels
must take.

> The **routing rule** and the **gated action** are not negotiable — the answer key is written
> against them. Tool *names*, by contrast, are only suggestions. See `../docs/D2-tool-layer.md`.
