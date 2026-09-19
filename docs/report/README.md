# The report — six sections, 2,000 words

One file per section, named `S<n>-<slug>.md`. **ZHENG YONGJIE assembles** and owns the final count.

**Section titles, order and budgets are the brief's, not ours** (§4 · *What you submit*, p.18).
Our earlier titles and split are superseded; `PLAN.md` §6 records what we originally planned.
**The per-section budget is guidance; the 2,000-word total is a limit.**

| § | Section (the brief's title) | Budget | Actual | Owner | File |
|---|---|---:|---:|---|---|
| 1 | Why an agent | 400 | 399 | ZHENG YONGJIE | ✅ `S1-why-an-agent.md` |
| 2 | The tool layer | 450 | 381 | Goncalo Miranda | ✅ `S2-the-system-we-built.md` |
| 3 | What the evidence showed | 350 | 348 | NIU TONG | ✅ `S3-evaluation-and-results.md` |
| 4 | What it costs | 400 | 412 | WANG HONGJUN | ✅ `S4-cost-to-serve.md` |
| 5 | The two failures | 250 | 298 | SUN YUCONG | ✅ `S5-what-broke.md` |
| 6 | What we would not deploy | 150 | 150 | JIN CHENG | ✅ `S6-the-architecture-we-did-not-build.md` |
| | **Total** | **2,000** | **1,988** | | |

> **§4 and §5 run over their guidance, and §2 under.** Both failures had to fit in §5 — the brief
> asks for the loop failure *and* the second, and §5 originally carried only one — and §2 paid for
> it. The brief notes that §1 and §2 together should be about 850 because Conceptual Understanding
> and Reasoning & Justification are half the rubric; ours are 780. **Twelve words remain unused.
> They belong in §2 if anyone spends them.**

**Filenames are deliberately not renamed.** Git history ties each file to its author, and
individual marks are adjusted against that history (`PLAN.md` §7). The heading inside each file
carries the brief's title; the filename carries the provenance.

**Prose, not bullets.** Six differently-voiced fragments read like six projects, and Communication
is a marked criterion. Write paragraphs and let ZHENG YONGJIE smooth the joins.

**Tables and figures do not count** toward the 2,000 words. If a number is better shown than
described, table it and spend the prose on what it means.

**What is marked is Reasoning & Justification.** The brief's own words: *"a cost model that only
reports a number says nothing about our design."* That applies to every section. Say what you
chose, what you rejected, and what the evidence made you change your mind about. We have a lot of
the third kind — fourteen overclaims found in D0, a poka-yoke downgraded in seven places, a
delisted model caught the day before the battery, a harness bug that cost SUN YUCONG 61 trials,
and a guardrail row that still fails. **Every defect we found was ours.** That is the honest
through-line of this project and it is worth more than a clean result would have been.

**Check your numbers against the repository before you write them.** Every figure in the report
should be reproducible from a committed file. If you cannot point at the file, do not write the
number. Every figure in all six sections has been checked against its source file.

---

## Still outstanding for the submission

The report is four of the brief's artefacts away from complete. From §4 of the brief:

| # | Artefact | State |
|---|---|---|
| 1 | Code repository — in **two** places: the public GitHub repo **and** a copy inside the NTULearn folder | repo ✅ · NTULearn copy ❌ |
| 2 | Team report — at most 2,000 words | ✅ 1,988 |
| 3 | Recorded demonstration — **5 minutes**, one negative case shown **live**, the numbers, **every member speaks** | ❌ not assembled |
| 4 | Team self-appraisal — one collective sheet, team rated against Rubric 1 plus a reflection on trade-offs | ❌ **does not exist** |

All four go in one archive, **`PE6201_A2_B-7.zip`**, plus the video link.

> The self-appraisal is ungraded but **a missing one makes the submission incomplete**. The
> template is on NTULearn. Rubric 1 is Conceptual Understanding 25% · Technical Execution 30% ·
> Reasoning & Justification 25% · Communication & Clarity 20%.
