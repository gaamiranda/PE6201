# src — the agent

D1, D2, D3(a). Keep this as `.py` modules, not one large notebook: notebook merges are brutal with
seven contributors, and the loop is the thing being marked.

Suggested shape (rename freely — nothing in the marking rewards keeping our layout):

| File | Holds |
|---|---|
| `config.py` | The single `BACKEND` / `MODEL` / `BASE_URL` block. `BACKEND = "scripted"` is the **default**. |
| `backends.py` | Exactly **one** function that knows a vendor exists. Switching model is a string. |
| `loop.py` | The ReAct loop. Parses an `Action:` **block**, executes each call, appends every observation. |
| `tools.py` | The tool set, each carrying its six-field descriptor as its docstring. |
| `guardrails.py` | Step cap, budget ceiling, action de-duplication, the autonomy gate. |

**Not in scope, and each is a way to run out of time:** a framework that owns the loop (LangChain,
LangGraph, CrewAI, AutoGen), multi-agent anything, fine-tuning, a UI, a letter or document
generator, a booking application, real email, a database server, a deployment.

**The gated action is a log entry.** One function, three steps: check the gate, append one
structured record to a local file, return a confirmation string. `issue_decision_letter` does not
compose a letter; `book_slot` does not book anything.

> Write `docs/D0-why-an-agent.md` — including the five "what good looks like" statements — and
> commit it **before** the first commit in this directory. The commit history is checked.
