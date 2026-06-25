# System Design Document

## Architecture Overview

The system accepts complex user requests as plain strings, decomposes them into discrete atomic subtasks, assigns each subtask to a specialized agent, and executes them through an async pipeline with streaming outputs and failure handling.

The decomposition layer is implemented as a standalone Python package at `src/decomposer/`. It uses simple rule-based parsing (no black-box agent frameworks) and is designed so that NLP-based intent classification can be plugged in later without changing the pipeline shape.

## Decomposer Package

### Module layout

```
src/decomposer/
├── __init__.py      # Public exports
├── models.py        # ParsedRequest, Subtask, TaskStep, DecomposedTask, AgentType
├── patterns.py      # Keyword → agent mappings and regex patterns
├── parser.py        # Step 1: accept and normalize input, scan keywords
├── splitter.py      # Step 2: split into atomic subtasks
├── assigner.py      # Step 3: map subtasks → Retriever / Analyzer / Writer
└── decomposer.py    # Orchestrates parse → split → assign
```

### Decomposition pipeline (execution order)

```
User string
    ↓
decomposer.py   ← entry point (TaskDecomposer.decompose)
    ↓
parser.py       ← Step 1: parse input
    ↓
splitter.py     ← Step 2: split into subtasks
    ↓
assigner.py     ← Step 3: assign agents
    ↓
DecomposedTask  (subtasks + steps)
```

| Order | Module | Responsibility |
|-------|--------|----------------|
| 0 | `decomposer.py` | Wires the three stages together and returns a `DecomposedTask` |
| 1 | `parser.py` | Accepts the raw string, normalizes it, scans for action keywords |
| 2 | `splitter.py` | Breaks the request into atomic subtasks (one agent each) |
| 3 | `assigner.py` | Maps each subtask to Retriever, Analyzer, or Writer |

Supporting modules (`models.py`, `patterns.py`) define shared data structures and matching rules. They are imported by the pipeline stages but do not run as separate execution steps.

### Step 1 — Parse (`parser.py`)

- Accepts the user's request as a string.
- Normalizes input (trim whitespace) into a `ParsedRequest`.
- Scans text for action keywords and verbs (e.g. fetch, analyze, summarize, write).
- Extracts a leading verb as a fallback when explicit keywords are absent.

Uses simple token and regex matching today. NLP tokenization can replace this stage later.

### Step 2 — Split (`splitter.py`)

- Takes a `ParsedRequest` and produces a list of atomic `Subtask` objects.
- Each subtask is small enough for a single agent.
- Splits on sentence boundaries, semicolons, commas, `and`, `then`, and numbered lists.
- Further splits compound phrases when each part maps to a different agent.

Example:

```
"Fetch 10 papers, extract key points, and generate a report."
  → Subtask 1: "Fetch 10 papers"
  → Subtask 2: "extract key points"
  → Subtask 3: "generate a report"
```

### Step 3 — Assign (`assigner.py`)

- Maps each subtask to an agent using keyword and verb matching.
- Records matched keywords on each `TaskStep` for traceability.
- Falls back to a default Retriever → Analyzer → Writer pipeline when no keywords match.

Agent mapping:

| Agent | Role | Example keywords |
|-------|------|------------------|
| **Retriever** | Data fetching tasks | fetch, retrieve, get, load, search, read |
| **Analyzer** | Processing and interpretation tasks | analyze, extract, summarize, classify, evaluate |
| **Writer** | Formatting and output generation tasks | write, generate, report, draft, format |

Example assignment:

```
"Fetch 10 papers"      → Retriever
"Extract key points"   → Analyzer
"Generate report"      → Writer
```

### Data models (`models.py`)

| Type | Purpose |
|------|---------|
| `AgentType` | Enum: `retriever`, `analyzer`, `writer` |
| `ParsedRequest` | Normalized user input (`original`, `normalized`) |
| `Subtask` | One atomic unit of work (`description`, `source_clause`) |
| `TaskStep` | Subtask assigned to an agent (`order`, `agent`, `description`, `matched_keywords`) |
| `DecomposedTask` | Full plan (`original_request`, `subtasks`, `steps`, `agent_sequence`) |

### Extension point

`AgentAssigner.match_agent()` is the hook for future NLP-based intent classification. Override this method to swap in spaCy, an LLM classifier, or another backend without changing the parse → split → assign pipeline.

## Agents

- **Retriever**: Fetches input data.
- **Analyzer**: Processes and interprets data.
- **Writer**: Generates structured output.

## End-to-end data flow

```
User Request (string)
    ↓
TaskDecomposer.decompose()
    ↓
Parse → Split → Assign
    ↓
DecomposedTask (ordered TaskSteps)
    ↓
Agent Pipeline (Retriever → Analyzer → Writer)
    ↓
Stream Output
    ↓
Failure Handling
```

## Execution Model

- Async pipeline using Python `asyncio` (`src/pipeline/`).
- Manual batching in `pipeline/batching.py` (default: 2 papers per batch).
- Streaming partial results via async generators (`StreamEvent`).

## Failure Handling

- Each agent wrapped in `run_agent_safe()` (`pipeline/failure.py`).
- Fallback paths: cached data (Retriever), partial analysis (Analyzer), partial report (Writer).
- Pipeline continues after agent failures; see `docs/design.md` for diagrams.
