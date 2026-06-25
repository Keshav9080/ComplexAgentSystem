# Video Script — Complex Agent System (Full Demo + Post-Mortem)

**Target length:** 3–5 minutes (~4 min 50 sec)  
**Audience:** Evaluators / technical reviewers  
**Repo:** https://github.com/Keshav9080/ComplexAgentSystem  

**Deliverables covered in this video:**
- System running live (decomposition + pipeline)
- At least one failure case with recovery
- Brief post-mortem: scaling issue, hindsight design change, two trade-offs

---

## Before you record

**Setup (5 min before hitting record):**
```powershell
git clone https://github.com/Keshav9080/ComplexAgentSystem.git
cd ComplexAgentSystem\src
python main.py
python run_pipeline.py
```

**On screen:**
- Terminal font size: 18pt+
- Tabs ready: `src/` terminal | `docs/design.md` (optional) | `docs/post-mortem.md` (for closing section)
- Close notifications; crop personal folder paths if needed

**Slides (optional but polished):**
1. Title — project name + your name
2. Architecture — three layers (Decomposer → Agents → Pipeline)
3. End card — repo URL + doc links

---

## FULL SCRIPT

---

### [0:00 – 0:25] OPEN — Problem & solution

**ON SCREEN:** Title slide → cut to terminal in `ComplexAgentSystem\src`

**SAY:**

> Hi, I'm **[Your Name]**. This video walks through my **Complex Agent System** — an agentic pipeline for multi-step tasks.
>
> A user sends one string, like *"Fetch 10 papers, extract key points, and generate a report."* The system **decomposes** that into steps, routes each step to a **specialized agent**, runs an **async pipeline** with **manual batching**, **streams partial results**, and **survives agent failures** without crashing.
>
> I'll show it running live, including a failure case, then briefly cover what I'd change at scale.

---

### [0:25 – 1:05] ARCHITECTURE — Three layers, no black box

**ON SCREEN:** `docs/design.md` diagram *or* speak over blank terminal

**SAY:**

> Three layers, all plain Python — no LangChain or CrewAI.
>
> **Layer 1 — Decomposer** (`src/decomposer/`): parse the string, split into atomic subtasks, assign keywords like *fetch*, *extract*, and *generate* to agents.
>
> **Layer 2 — Agents** (`src/agents/`): **Retriever** fetches data, **Analyzer** processes it, **Writer** builds the final report.
>
> **Layer 3 — Pipeline** (`src/pipeline/`): async execution, **manual batching** — two papers per batch instead of ten at once — streaming after each batch, and **failure wrappers** with fallbacks in `failure.py`.
>
> Data flow: **User request → Decompose → Batch loop → Stream → Final report.**

**ACTION:** Focus terminal at `src>` prompt.

---

### [1:05 – 1:50] DEMO 1 — Decomposition

**ON SCREEN:** Terminal

**TYPE:**
```powershell
python main.py
```

**SAY (as output appears):**

> First, decomposition only. `main.py` runs three example requests; focus on the first one.
>
> Input: *Fetch 10 papers, extract key points, and generate a report.*
>
> The splitter produces **three atomic subtasks**. The assigner maps them:
> - **Retriever** — matched keyword `fetch`
> - **Analyzer** — matched keyword `extract`
> - **Writer** — matched keywords `generate`, `report`
>
> This is **rule-based parsing** — deterministic and debuggable. NLP can plug in later via `AgentAssigner.match_agent()` without rewriting the pipeline.

**PAUSE ON SCREEN:**
```
  1. [retriever] (fetch) -> Fetch 10 papers
  2. [analyzer] (extract) -> extract key points
  3. [writer] (generate, report) -> generate a report
```

---

### [1:50 – 2:50] DEMO 2 — Happy path: batching + streaming

**ON SCREEN:** Terminal

**TYPE:**
```powershell
python run_pipeline.py
```

**SAY:**

> Now the full pipeline. Demo 1 is the **happy path**.
>
> Same request, same three steps — then execution. Ten papers become **five batches of two** because `batch_size=2` in `pipeline/batching.py`. That's **manual batching** — explicit lists like `[1,2]`, `[3,4]`, not a hidden library.
>
> Watch the event stream:
> - **`batch_start`** — a new batch is beginning
> - **`partial`** — Retriever and Analyzer finished for that batch; progress streams to the user
> - After all five batches, **`final`** — Writer produces the complete report
>
> Five partial updates, one final output. That's the async streaming model.

**PAUSE ON SCREEN:**
```
  [batch_start] [batch 0] Processing batch 1/5: papers [1, 2]
  [partial] [batch 0] Completed batch 1: 2 analyses ready
  ...
  [final] Pipeline complete
```

---

### [2:50 – 3:45] DEMO 3 — Failure case (required) ⭐

**ON SCREEN:** Same terminal — scroll to **Demo 2: Failure recovery** section

**SAY:**

> Demo 2 in the same script simulates a **Retriever failure on batch 1** — papers 3 and 4. Config: `retriever_fail_batches={1}`.
>
> Batch 0 succeeds. Batch 1 — Retriever **throws**. A naive pipeline stops here.
>
> Ours prints **`batch_failed`** with **`(recovered)`**. `run_agent_safe()` in `failure.py` catches the error and calls **`retriever_fallback()`** — cached metadata for those papers.
>
> Analyzer still runs. Batches 2 through 4 succeed. Writer still emits **`final`**. **One agent failed; the pipeline completed.**
>
> That's the **fallback-over-fail-fast** trade-off I'll mention in the post-mortem — resilience over perfect data in edge cases.

**PAUSE ON SCREEN:**
```
  [batch_failed] [batch 1] (recovered) Retriever failed on batch 1; using cache fallback
  [partial] [batch 1] Completed batch 2: 2 analyses ready
  ...
  [final] Pipeline complete
```

**OPTIONAL (10 sec):** Quick flash of `src/pipeline/failure.py` → `run_agent_safe()`.

---

### [3:45 – 4:35] POST-MORTEM — Scaling, hindsight, trade-offs

**ON SCREEN:** `docs/post-mortem.md` (scroll to each heading as you speak)

**SAY:**

> Quick post-mortem — full write-up in `docs/post-mortem.md`.
>
> **Scaling issue:** Batches run **sequentially** today. Fine for ten simulated papers; at a hundred or a thousand with real API calls, runtime grows linearly and concurrency sits idle. I'd add parallel batches with a concurrency cap and persistent checkpointing to resume mid-run.
>
> **Design change in hindsight:** I'd introduce one shared **`PipelineState`** object passed between agents instead of scattered dict payloads and re-parsing *"Fetch 10 papers"* in the executor. Cleaner recovery, easier tests, same public API.
>
> **Trade-off one — parsing:** Rule-based keywords vs NLP. I chose regex for **transparency and zero dependencies**; cost is brittle phrasing like *"grab ten articles."*
>
> **Trade-off two — failures:** Fallback recovery vs fail-fast. I chose **always complete with degraded data** so the demo and long jobs stay resilient; production would add retries and explicit `source=fallback` flags on every artifact.

---

### [4:35 – 5:00] CLOSE — Repo & docs

**ON SCREEN:** End card

```
https://github.com/Keshav9080/ComplexAgentSystem

docs/design.md          — architecture & diagrams
docs/post-mortem.md     — scaling, hindsight, trade-offs
docs/System Design Document.md
src/run_pipeline.py     — live demo
```

**SAY:**

> You saw decomposition, manual batching, streaming, and failure recovery — all in explicit Python.
>
> Code and docs are on GitHub. Thanks for watching.

---

## Timing card

| Segment | Time | Running total |
|---------|------|---------------|
| Open | 0:25 | 0:25 |
| Architecture | 0:40 | 1:05 |
| Demo 1 — Decompose | 0:45 | 1:50 |
| Demo 2 — Happy path | 1:00 | 2:50 |
| Demo 3 — Failure | 0:55 | 3:45 |
| Post-mortem | 0:50 | 4:35 |
| Close | 0:25 | **5:00** |

**Too long?** Trim post-mortem to 30 sec (scaling + one trade-off only).  
**Too short?** Expand failure demo with 10 sec on `failure.py` code.

---

## Commands reference (copy-paste)

```powershell
cd ComplexAgentSystem\src
python main.py
python run_pipeline.py
```

---

## Lower-thirds / captions to add in edit

| Timestamp | Label |
|-----------|-------|
| 1:05 | `Step 1: Decomposer` |
| 1:50 | `Step 2: Pipeline — batch_size=2` |
| 2:50 | `FAILURE → RECOVERED` |
| 3:45 | `Post-Mortem` |
| End | `github.com/Keshav9080/ComplexAgentSystem` |

---

## Q&A backup (not in video — for live Q&A or description box)

| Question | Answer |
|----------|--------|
| Why no agent framework? | Task requires showing what's under the hood; I own parsing, batching, and fallbacks. |
| Where is batching implemented? | `src/pipeline/batching.py` — `manual_batches(10, 2)`. |
| Where is failure handling? | `src/pipeline/failure.py` — `run_agent_safe()` + per-agent fallbacks. |
| How to scale? | Parallel batches, retries before fallback, `PipelineState` persistence. |
| Where is the post-mortem doc? | `docs/post-mortem.md`. |

---

## Submission checklist

- [ ] Video is 3–5 minutes
- [ ] Shows system **running** (`main.py` + `run_pipeline.py`)
- [ ] Shows **at least one failure case** with recovery visible on screen
- [ ] Mentions or shows post-mortem (scaling + trade-offs)
- [ ] Upload unlisted (YouTube / Loom) and add link to README or submission
