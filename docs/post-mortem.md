# Post-Mortem — Complex Agent System

This document reflects on building the multi-agent pipeline: what would break at scale, what we would change in hindsight, and the trade-offs we accepted along the way.

---

## Scaling issue (encountered / anticipated)

### Sequential batch execution limits throughput

**Issue:** The pipeline processes batches **one at a time** in `PipelineExecutor.run()`. For a request like *"Fetch 10 papers…"* with `batch_size=2`, five batches run sequentially — each batch waits for Retriever and Analyzer to finish before the next batch starts.

**Why it matters at scale:** At 100 or 1,000 papers (or real network I/O to external APIs), total runtime grows linearly with batch count. Retriever and Analyzer work within a batch is independent of other batches, so serial execution underuses available concurrency and becomes a bottleneck long before agent logic fails.

**Evidence from the current design:** `docs/design.md` explicitly documents sequential batches for traceability. `run_pipeline.py` demo with 10 papers and `batch_size=2` completes quickly because agents use simulated `asyncio.sleep(0.05)` — the bottleneck is hidden until real I/O or larger workloads are introduced.

**Mitigation we would pursue:**
- Run batches with `asyncio.gather()` and a configurable concurrency limit (e.g. max 3 batches in flight).
- Add backpressure so Retriever rate limits are not exceeded.
- Persist batch results incrementally so a crash mid-run can resume from the last completed batch rather than restarting all N papers.

---

## Design change in hindsight

### Introduce a shared `PipelineState` object earlier in the design

**What we built:** Context is split across `PipelineContext` (batch metadata, aggregated analysis), per-agent payloads (dicts passed to `run()`), and `StreamEvent` objects for output. The decomposer produces a `DecomposedTask`; the executor re-parses fetch count from the Retriever step description via regex in `batching.py`.

**What we would change:** Define a single **`PipelineState`** dataclass at the start of execution that holds:
- the decomposed plan,
- parsed parameters (item count, batch size),
- accumulated results per stage,
- error/fallback log,

and pass **only that object** between agents. Agents would read/write named slots (e.g. `state.retrieved`, `state.analyzed`) instead of ad-hoc dict payloads.

**Why:**
- Avoids re-parsing `"Fetch 10 papers"` in the executor when the decomposer already understood the request.
- Makes failure recovery and partial reruns easier — reload state from batch *k* without reconstructing payloads.
- Simplifies testing: one structure to assert on instead of tracing dict shapes through three agent modules.

This refactor would not change the external API (`AgentPipeline.run(request)`) but would reduce coupling between decomposition and execution layers.

---

## Trade-off 1: Rule-based parsing vs NLP-based decomposition

| | Choice made | Alternative |
|---|-------------|-------------|
| **Decision** | Keyword/regex parsing in `decomposer/` (`patterns.py`, `assigner.py`) | spaCy, LLM intent classification, or an agent framework |
| **Reasoning** | Task requirement: show understanding under the hood — no black-box framework without justification. Regex is deterministic, debuggable, and zero-dependency. |
| **Cost** | Fragile on paraphrasing (*"grab ten articles"* may not map to Retriever). Requires maintaining keyword lists. |
| **Benefit** | Fast, reproducible, easy to demo and unit test. Clear extension point via `AgentAssigner.match_agent()` when NLP is added later. |

**We accepted lower linguistic flexibility in exchange for transparency and control.** For a production system with varied user phrasing, we would add NLP behind the same assigner interface rather than replace the pipeline.

---

## Trade-off 2: Fallback recovery vs fail-fast correctness

| | Choice made | Alternative |
|---|-------------|-------------|
| **Decision** | On agent failure, `run_agent_safe()` in `failure.py` catches exceptions and returns fallback data (cached papers, minimal analysis, partial report). Pipeline always completes. | Fail fast: abort the pipeline, surface error to user, require retry |
| **Reasoning** | Deliverable requirement: pipeline must not break when one agent fails. Demo in `run_pipeline.py` shows Retriever failure on batch 1 recovered via `retriever_fallback()`. |
| **Cost** | Final output may include **lower-quality or misleading data** (e.g. cached titles instead of live fetches) without the user clearly knowing unless they read `batch_failed` events. |
| **Benefit** | Resilience and partial progress — batches 0, 2–4 still produce real analysis; Writer still delivers a report. Better for long-running jobs where some data is better than none. |

**We accepted semantic accuracy in edge cases in exchange for availability and demo reliability.** A production version would add: retry with exponential backoff before fallback, explicit `confidence` / `source` flags on every artifact, and a user-visible summary of which batches used fallbacks.

---

## Summary

| Guideline | Addressed in |
|-----------|--------------|
| One scaling issue | Sequential batch execution (above) |
| One hindsight design change | Unified `PipelineState` (above) |
| Two trade-offs with reasoning | Parsing vs NLP; fallback vs fail-fast (above) |

Related docs: `docs/design.md` (architecture), `docs/System Design Document.md` (overview), `docs/video-script.md` (demo including failure case).
