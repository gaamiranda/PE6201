# The report — six sections, 2,000 words

One file per section, named `S<n>-<slug>.md`. Owners and word budgets are in
[`../../PLAN.md`](../../PLAN.md) §6. **ZHENG YONGJIE assembles** and owns the final count.

| § | Section | Words | Owner | File |
|---|---|---|---|---|
| 1 | Why an agent at all | 350 | ZHENG YONGJIE | `S1-why-an-agent.md` |
| 2 | The system we built | 300 | Goncalo Miranda | ✅ `S2-the-system-we-built.md` |
| 3 | Evaluation and results | 350 | NIU TONG | `S3-evaluation-and-results.md` |
| 4 | Cost to serve | 400 | WANG HONGJUN | `S4-cost-to-serve.md` |
| 5 | What broke, and what we changed | 350 | SUN YUCONG | ✅ `S5-what-broke.md` |
| 6 | The architecture we did not build | 250 | JIN CHENG | `S6-the-architecture-we-did-not-build.md` |

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
number.
