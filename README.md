# Complex Agent System

An agentic AI system that accepts a complex, multi-part request, decomposes it into discrete ordered steps, assigns each step to a specialized agent, executes them through an async pipeline with **manual batching**, **streams partial results**, and **recovers gracefully when an agent fails**.

Built with explicit, readable Python — **no black-box agent frameworks** — so the decomposition, batching, and failure-handling logic is fully visible under the hood.

## Features

- **Request decomposition** — turns a single string into atomic, ordered subtasks
- **Specialized agents** — Retriever, Analyzer, and Writer, each with a single responsibility
- **Async pipeline** — built on `asyncio` with streaming partial outputs
- **Manual batching** — processes large jobs in fixed-size batches (e.g. 2 papers at a time, not all 10)
- **Failure handling** — every agent runs inside a safe wrapper with per-agent fallbacks; one failure never crashes the pipeline
- **Rule-based parsing** — deterministic keyword matching today, with a clean hook to plug in NLP later

## Architecture

The system has three layers:

```
User request (string)
        │
        ▼
  decomposer/   ── parse → split into subtasks → assign agents
        │
        ▼
  pipeline/     ── manual batching → async execution → streaming → fallbacks
        │
        ▼
  agents/       ── Retriever → Analyzer → Writer
        │
        ▼
  Streamed events + final report
```

| Layer | Package | Responsibility |
|-------|---------|----------------|
| Decompose | `src/decomposer/` | Parse the request, split into atomic subtasks, assign each to an agent |
| Execute | `src/pipeline/` | Batch work, run agents async, stream results, handle failures |
| Agents | `src/agents/` | Retriever (fetch), Analyzer (process), Writer (output) |

## Project structure

```
ComplexAgentSystem/
├── README.md
├── .gitignore
├── docs/
│   ├── System Design Document.md   # High-level architecture overview
│   ├── design.md                   # Pipeline design with diagrams
│   ├── post-mortem.md              # Scaling issue, hindsight, trade-offs
│   └── demo.mp4                     # Generated visual walkthrough
└── src/
    ├── main.py                      # CLI demo: decomposition only
    ├── run_pipeline.py              # CLI demo: full pipeline + failure case
    ├── generate_demo_video.py       # Generates docs/demo.mp4
    ├── decomposer/                  # Parse → split → assign
    │   ├── parser.py
    │   ├── splitter.py
    │   ├── assigner.py
    │   ├── decomposer.py
    │   ├── patterns.py
    │   └── models.py
    ├── agents/                      # Retriever / Analyzer / Writer
    │   ├── base.py
    │   ├── retriever.py
    │   ├── analyzer.py
    │   ├── writer.py
    │   └── registry.py
    └── pipeline/                    # Execution, batching, failure handling
        ├── pipeline.py
        ├── executor.py
        ├── batching.py
        ├── failure.py
        └── models.py
```

## Requirements

- **Python 3.10+** (uses `X | None` type syntax)
- Core pipeline uses only the **standard library** (`asyncio`, `re`, `dataclasses`)
- Optional, only for `generate_demo_video.py`:
  - `opencv-python`
  - `imageio-ffmpeg`
  - `Pillow`

## Installation

```bash
git clone https://github.com/Keshav9080/ComplexAgentSystem.git
cd ComplexAgentSystem
```

To run the optional video generator, install the extra dependencies:

```bash
pip install opencv-python imageio-ffmpeg Pillow
```

## Usage

All entry points live in `src/`, so run them from there:

```bash
cd src
```

**1. Task decomposition only**

```bash
python main.py
```

Shows how a request is split into subtasks and assigned to agents:

```
Request: Fetch 10 papers, extract key points, and generate a report.

  Subtasks:
    1. Fetch 10 papers
    2. extract key points
    3. generate a report

  Assigned steps:
    1. [retriever] (fetch) -> Fetch 10 papers
    2. [analyzer] (extract) -> extract key points
    3. [writer] (generate, report) -> generate a report
```

**2. Full pipeline (batching, streaming, failure recovery)**

```bash
python run_pipeline.py
```

Runs two demos — a happy path and a Retriever failure on batch 1 that is recovered via a cache fallback:

```
  [batch_start] [batch 1] Processing batch 2/5: papers [3, 4]
  [batch_failed] [batch 1] (recovered) Retriever failed on batch 1; using cache fallback
  [partial] [batch 1] Completed batch 2: 2 analyses ready
  ...
  [final] Pipeline complete
```

**3. Use the pipeline in your own code**

```python
import asyncio
import json
from pipeline import AgentPipeline

async def main():
    pipeline = AgentPipeline(batch_size=2)
    async for event in pipeline.run(
        "Fetch 10 papers, extract key points, and generate a report."
    ):
        print(event.event_type.value, event.message)
        if event.event_type.value == "final":
            print(json.dumps(event.data, indent=2))  # the full report

asyncio.run(main())
```

## How it works

### Decomposition (`decomposer/`)
1. **Parse** — accept and normalize the request, scan for action keywords (`fetch`, `analyze`, `write`, …)
2. **Split** — break the request into atomic subtasks on sentence/clause boundaries
3. **Assign** — map each subtask to an agent by keyword (Retriever / Analyzer / Writer), falling back to a default pipeline when nothing matches

### Manual batching (`pipeline/batching.py`)
A request like *"Fetch 10 papers"* is split into explicit batches — e.g. `[[1,2], [3,4], [5,6], [7,8], [9,10]]` with `batch_size=2`. No hidden batching abstraction.

### Failure handling (`pipeline/failure.py`)
Every agent call goes through `run_agent_safe()`, which catches exceptions and applies an agent-specific fallback:

| Agent | Fallback |
|-------|----------|
| Retriever | Cached paper metadata |
| Analyzer | Minimal key points noting the failure |
| Writer | Partial report with collected analysis |

Failures surface as `StreamEvent`s with `recovered=True`, and the pipeline continues to completion.

## Extending with NLP

The keyword-based assigner is a deliberate first step. To swap in NLP-based intent classification (spaCy, an LLM, etc.), override `AgentAssigner.match_agent()` — the parse → split → assign pipeline shape stays the same.

## Documentation

- [`docs/System Design Document.md`](docs/System%20Design%20Document.md) — architecture overview
- [`docs/design.md`](docs/design.md) — pipeline design with Mermaid diagrams
- [`docs/post-mortem.md`](docs/post-mortem.md) — scaling issue, hindsight design change, and trade-offs

## License

MIT License
