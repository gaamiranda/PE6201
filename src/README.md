# src — the agent

**Owners:** Goncalo Miranda · ZHENG YONGJIE (loop and tools) · SUN YUCONG (guardrail layer).
*Deadlines and dependencies: [`../PLAN.md`](../PLAN.md).*

D1, D2, D3(a). Keep this as `.py` modules, not one large notebook: notebook merges are brutal with
six contributors, and the loop is the thing being marked.

**Start from [`contracts.py`](contracts.py).** It is already committed and frozen: the decision
record, the answer-key row, the trial result, the `run_case` seam and the vendor seam. Four people
are coding against it, so add fields rather than renaming them.

Suggested shape (rename freely — nothing in the marking rewards keeping our layout):

| File | Holds |
|---|---|
| `contracts.py` | ✅ **committed.** The shared types, the `BACKEND` / `MODEL` / `BASE_URL` block, and the two seams. `BACKEND = "scripted"` is the **default**. |
| `backends.py` | Exactly **one** function that knows a vendor exists. Switching model is a string. |
| `loop.py` | The ReAct loop. Parses an `Action:` **block**, executes each call, appends every observation. |
| `tools.py` | The tool set, each carrying its six-field descriptor as its docstring. |
| `guardrails.py` | Step cap, budget ceiling, action de-duplication, the autonomy gate. |

**Not in scope, and each is a way to run out of time:** a framework that owns the loop (LangChain,
LangGraph, CrewAI, AutoGen), multi-agent anything, fine-tuning, a UI, a letter or document
generator, a booking application, real email, a database server, a deployment.

**Tool names in Appendix A are suggestions, not an interface.** Rename, merge, split or add as the
design requires — you cannot write an honest six-field descriptor for a signature somebody else
fixed. The **routing rule** and the **gated action** are the parts that are fixed, because the
answer key is written against them.

**The gated action is a log entry.** One function, three steps: check the gate, append one
structured record to a local file, return a confirmation string. `issue_decision_letter` does not
compose a letter; `book_slot` does not book anything.

> Write `docs/D0-why-an-agent.md` — including the five "what good looks like" statements — and
> commit it **before** the first commit in this directory. The commit history is checked.
