# fixtures — local data the tools read

Small local files standing in for the systems of record. JSON, CSV, or a small SQLite file.
**No live systems and no real accounts** — nothing the agent touches may be somebody's actual record.

## Two conditions

1. **Keep the records the instructor's generator supplied.** A marker re-runs our harness against them.
2. **Commit whatever generates or holds our additions**, so the data set is reproducible rather than
   a mystery.

## Guide to size

30–60 primary records (claims / referrals) plus the supporting rows they reference. Enough to make
the evaluation set meaningful and no more.

## The thing that silently breaks everything

The files connect to one another, and that is how the agent gets from one fact to the next. A claim
carries a `member_id`; the members file is keyed by that same `member_id`. **Invent a claim whose
`member_id` matches nobody and the agent will look perfectly sound and return nothing.**

Extending the fixtures deliberately to create a negative case is good practice and worth mentioning
in the report.

## Answer key

`expected_outcomes_A.json` / `_B.json` give the outcome the Appendix A routing table requires and the
single trigger that produces it. That is the ground truth for D4, and the shape our own labels must take.
