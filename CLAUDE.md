# CLAUDE.md

This file defines the project layout, conventions, and tooling for this Python package.
Claude Code must follow these rules exactly when creating, editing, or refactoring files.

- **Package**: `scrutiny` — import as `from scrutiny.models import Chunk`
- **Repo**: `scrutiny`

---

## Project Overview

The Playground is a Streamlit-based experimentation environment for power-users to
design, evaluate, and refine **supervisory checks** — rules that detect and classify
specific disclosures in public prospectus documents.

A supervisory check is a pipeline of three sequential, independently configurable steps:

1. **Chunking** — splitting document text into candidate spans (sentence, paragraph, token window, or regex boundary)
2. **Detection** — filtering chunks using regex, Azure AI Search, or hybrid
3. **Classification** — evaluating chunks against an LLM prompt template via Azure OpenAI

Each step is configured via its own **YAML file**. All inputs and outputs are YAML — never JSON.

The Playground reuses the same modules as production (`src/scrutiny/chunking/`,
`detection/`, `classification/`). It is **not** a production service — it is an analyst
tool for iterative testing and side-by-side comparison of check behaviour.

---

## Streamlit App Structure

Multi-page app using the `pages/` convention. Each page owns one pipeline step.

```
src/scrutiny/app/
├── Home.py                  # Entry point: document upload + check name input
├── pages/
│   ├── 1_Chunking.py        # Chunking config editor + preview of produced chunks
│   ├── 2_Detection.py       # Detection config editor + preview of matched chunks
│   ├── 3_Classification.py  # Prompt template editor + preview of classifications
│   └── 4_Results.py         # Full output viewer, YAML download, run comparison
└── components/
    ├── yaml_editor.py       # Reusable: text_area + file_uploader + download_button
    ├── chunk_viewer.py      # Reusable: renders a list of Chunk objects as a table
    └── banner.py            # Reusable: demo mode warning banner
```

### Page data flow

| Page | Reads | Writes |
|---|---|---|
| `Home.py` | — | `document`, `document_name`, `check_name` |
| `1_Chunking.py` | `document` | `chunking_config`, `chunks` |
| `2_Detection.py` | `chunks` | `detection_config`, `matched_chunks` |
| `3_Classification.py` | `matched_chunks` | `classification_config`, `results` |
| `4_Results.py` | `chunks`, `matched_chunks`, `results`, all configs | `run_history` |

### Session state keys — use exactly these, never invent new ones

| Key | Type | Description |
|---|---|---|
| `document` | `bytes` | Raw PDF bytes from file uploader |
| `document_name` | `str` | Original filename of the uploaded PDF |
| `check_name` | `str` | Supervisory check name (used as configs folder name) |
| `chunking_config` | `dict` | Parsed `chunking.yaml` |
| `detection_config` | `dict` | Parsed `detection.yaml` |
| `classification_config` | `dict` | Parsed `classification.yaml` |
| `chunks` | `list[Chunk]` | Chunks from the chunking step |
| `matched_chunks` | `list[MatchedChunk]` | Chunks from the detection step |
| `results` | `list[ClassificationResult]` | Classification output per matched chunk |
| `demo_mode` | `bool` | UX demo mode active (sidebar toggle) |
| `run_history` | `list[dict]` | Previous run outputs for comparison |

### Sidebar (rendered on every page)

Always shows: current document name (or "No document loaded"), current check name
(or "No check selected"), `🧪 Demo mode` toggle, yellow warning banner when demo
mode is active (via `components/banner.py`).

---

## Data Models

Defined in `src/scrutiny/models.py`. All data passed between pipeline steps
uses these **dataclasses** — never plain dicts.

- `Chunk` — fields: `text`, `chunk_index`, `page_number: int | None`, `start_char`, `end_char`, `metadata: dict`
- `MatchedChunk` — fields: `chunk: Chunk`, `score: float` (0.0–1.0; regex → 1.0), `engine: str` ("regex" | "azure_ai_search" | "hybrid")
- `ClassificationResult` — fields: `matched_chunk`, `output_fields: dict[str, str]` (always includes "decision" YES|NO and "justification"), `model: str`, `is_stub: bool`

See `models.py` for the full definitions with docstrings.

---

## Adapter Interfaces

Defined in `src/scrutiny/adapters/base.py`. Every real and stub implementation
must subclass these exactly — never add extra public methods.

- `SearchAdapter.search(chunks: list[Chunk], config: dict) -> list[MatchedChunk]`
- `ClassificationAdapter.classify(matched_chunks: list[MatchedChunk], config: dict) -> list[ClassificationResult]`

See `adapters/base.py` for full ABCs with numpy docstrings.

---

## YAML Configuration

All inputs and outputs are YAML. This is a hard requirement — no JSON anywhere in
the UI or pipeline.

### File layout

```
configs/<check_name>/
├── chunking.yaml
├── detection.yaml
├── classification.yaml
└── output_<timestamp>.yaml    # Generated after each run
```

### Input schemas (key → type → allowed values)

**`chunking.yaml`**: `method` (sentence | paragraph | token_window | regex_boundary),
`chunk_size` (int), `overlap` (int), `boundary_pattern` (str, only for regex_boundary)

**`detection.yaml`**: `engine` (regex | azure_ai_search | hybrid), `regex.patterns` (list[str]),
`regex.flags` (IGNORECASE | MULTILINE | DOTALL), `azure_ai_search.index_name` (str),
`azure_ai_search.query` (str), `azure_ai_search.top_k` (int)

**`classification.yaml`**: `adapter` (azure_openai), `model` (str), `temperature` (float),
`prompt_template` (str, uses `{{ chunk }}` and `{{ topic }}`), `output_fields` (list[str],
must include "decision" and "justification")

### Output schema (`output_<timestamp>.yaml`)

Top-level keys: `run` (timestamp, document_name, check_name, mode), `config` (full
copies of all three input configs), `results` (list of: chunk_index, page_number, text,
score, engine, decision, justification, is_stub). See existing output files for examples.

### YAML handling rules

- Editors: `st.text_area` pre-populated with schema defaults when empty
- Upload: `st.file_uploader` (.yaml/.yml) replaces editor content
- Validation: validate against schema before running; show **plain-English** errors
- Download: `st.download_button` for each config and for output YAML
- Parsing: `yaml.safe_load` / `yaml.dump` only. Never `yaml.load` without a Loader

---

## Azure Service Stubs

The codebase must be **fully functional without Azure credentials**. Both Azure AI
Search and Azure OpenAI have stub implementations.

### Run modes

| Mode | Activates when | Who uses it |
|---|---|---|
| Production | `PLAYGROUND_ENV=production` + Azure creds | Live deployment |
| Development | `PLAYGROUND_ENV=development` (default) | Local dev and CI |
| UX Demo | `demo_mode` sidebar toggle | Analysts evaluating UI |

Mode is resolved **once** in `src/scrutiny/config.py` via `resolve_config()` →
`RunConfig` dataclass. Adapters are created via `make_search_adapter()` and
`make_classification_adapter()` factory functions. See `config.py` for implementation.

### Stub behaviour summary

| Adapter | Dev mode | Demo mode |
|---|---|---|
| `StubSearchAdapter` | Runs regex patterns from config; falls back to returning all chunks | Returns first N chunks (default 3), score 0.85, engine "demo" |
| `StubClassificationAdapter` | Keyword heuristic; prefixes justification with `"[Dev mode] "` | First chunk → YES, rest → NO; quotes chunk text in justification |

Both stubs set `is_stub=True`. Demo mode shows a yellow banner on every page:
*"🧪 Demo mode active — results are simulated and do not reflect real detection behaviour."*

---

## Error Handling

- **UI layer**: catch all exceptions; show `st.error()` with plain-English messages. Never expose tracebacks, class names, or module paths to the user.
- **YAML validation**: raise `ValueError` with a human-readable message (e.g. "Chunking method must be one of: sentence, paragraph, token_window, regex_boundary"). Catch in the page and render with `st.error()`.
- **Adapter errors**: wrap Azure SDK calls in try/except; surface as `st.error("Could not connect to Azure AI Search. Check your credentials and try again.")`.
- **Logging**: use `logging.getLogger(__name__)` in all modules. Log at DEBUG for step inputs/outputs, WARNING for fallbacks, ERROR for caught exceptions. Never `print()`.

---

## Common Workflows

### Add a new chunking method

1. Add the implementation to `src/scrutiny/chunking/__init__.py` inside `chunk_document()`
2. Add the method name to the validation allow-list in `1_Chunking.py`
3. Add a test in `tests/scrutiny/test_chunking.py`
4. Update the `chunking.yaml` schema comment in this file

### Add a new detection engine

1. Implement a new `SearchAdapter` subclass in `src/scrutiny/adapters/`
2. Register it in `config.py` → `make_search_adapter()`
3. Add to the `engine` allow-list in `2_Detection.py`
4. Add stub + tests

### Add a new output field to classification

1. Add the field name to the `output_fields` list in `classification.yaml`
2. The `ClassificationAdapter.classify()` contract already returns `output_fields: dict[str, str]` — no code change needed unless the field requires special handling
3. Update `4_Results.py` if the field needs dedicated rendering

---

## Project Structure

```
scrutiny/
├── .gitignore
├── .pre-commit-config.yaml
├── .vscode/settings.json
├── .yamllint
├── MANIFEST.in
├── README.md
├── azure-pipeline.yaml
├── mkdocs.yaml
├── pyproject.toml
├── requirements.txt                          # Single line: "."
├── configs/<check_name>/*.yaml               # Supervisory check YAML configs
├── docs/
│   ├── index.md
│   ├── about.md
│   └── make_package_docs.py
├── src/scrutiny/
│   ├── __init__.py
│   ├── models.py                             # Chunk, MatchedChunk, ClassificationResult
│   ├── config.py                             # RunConfig, resolve_config(), adapter factories
│   ├── adapters/                             # base.py (ABCs), azure_*.py, stub_*.py
│   ├── chunking/__init__.py                  # chunk_document(text, config) -> list[Chunk]
│   ├── detection/__init__.py                 # run_detection(chunks, config, adapter) -> list[MatchedChunk]
│   ├── classification/__init__.py            # run_classification(matched, config, adapter) -> list[ClassificationResult]
│   ├── app/                                  # Home.py, pages/, components/
│   └── package_data/
└── tests/
    ├── conftest.py                           # Sets PLAYGROUND_ENV=development
    ├── data/                                 # Sample PDFs and fixture YAMLs
    └── scrutiny/                       # Mirrors src/ structure
```

---

## Dependencies & Tooling

- **Python**: 3.12. Use `X | Y` unions, `match` statements, dataclasses freely.
- **Package manager**: `uv`
- **Build backend**: setuptools, `src/` layout
- **Runtime deps**: streamlit, pdfplumber, PyYAML, azure-search-documents, azure-identity, openai — see `pyproject.toml` for pinned versions
- **Dev deps**: black, isort, pip-audit, pre-commit, pylint, pytest, pytest-cov, yamllint
- **Docs deps**: mkdocs + mkdocs-material + mkdocstrings-python

Azure SDK classes (`azure-search-documents`, `azure-identity`, `openai`) must only be
imported inside factory functions in `config.py` — never at module top level.

### Formatting & linting

- **black**: line length 88
- **isort**: `--profile black`, applied to `src/` and `tests/`
- **pylint**: applied to `src/` only
- **yamllint**: max line length 120, platform line endings
- **Docstrings**: numpy-style throughout (required by mkdocstrings)

### Pre-commit hooks

Hooks run on pre-commit: no-commit-to-branch (main/develop), mixed-line-ending,
trailing-whitespace, check-yaml, check-merge-conflict, isort, black, pylint, yamllint.
On pre-push: pip-audit. Install: `uv run pre-commit install`

### Git conventions

- **Protected branches**: `main`, `develop` (no direct commits)
- **Branch naming**: `feature/<short-description>`, `bugfix/<short-description>`, `hotfix/<short-description>`
- **Commit messages**: imperative mood, max 72 chars subject line (e.g. "Add token_window chunking method")
- **CI**: Azure Pipeline triggers on `main` and `develop`, pool `windows-2019`

---

## Testing

- Framework: **pytest** + **pytest-cov**
- `conftest.py` sets `PLAYGROUND_ENV=development` via `monkeypatch` for all tests
- Test files mirror `src/` under `tests/scrutiny/`
- Sample PDFs and fixture YAMLs go in `tests/data/`
- Tests **never** require Azure credentials or network access — stubs only
- Run: `uv run pytest` / with coverage: `uv run pytest --cov=src`

---

## Documentation

- Numpy docstrings auto-extracted by `mkdocstrings-python`
- `docs/make_package_docs.py` generates `docs/reference/` pages
- Serve: `uv sync --extra docs && uv run mkdocs serve`

---

## Quick Start

```shell
git clone <azure_url>
cd scrutiny
uv sync --extra dev
uv run pre-commit install

# Run the Streamlit app in dev mode (no Azure credentials needed)
PLAYGROUND_ENV=development uv run streamlit run src/scrutiny/app/Home.py
```

---

## Key Rules for Claude Code

1. **Source code lives under `src/scrutiny/`** — never at the root.
2. **Tests live under `tests/scrutiny/`** — never inside `src/`.
3. **All docstrings are numpy-style** — required for mkdocs API generation.
4. **Dependencies go in `pyproject.toml`** — never in `requirements.txt`.
5. **Line length is 88** — black standard, no exceptions.
6. **Use `uv`** as the package manager — never `pip` directly.
7. **All pipeline data uses dataclasses from `models.py`** — never plain dicts between steps.
8. **Session state uses only the keys listed above** — never invent new ones.
9. **All configs are YAML** — never JSON. `yaml.safe_load` / `yaml.dump` only.
10. **Validate YAML before running** — show plain-English errors, never tracebacks.
11. **Never import Azure SDKs at module top level** — only inside factory functions in `config.py`.
12. **`PLAYGROUND_ENV` is read only in `config.py`** — nowhere else.
13. **Tests never require Azure credentials** — stubs only, enforced by `conftest.py`.
14. **The UI is for non-technical analysts** — plain language everywhere, no tracebacks.
15. **Errors use `st.error()` with human-readable messages** — never expose internals.
16. **Use `logging` module** — never `print()`. Logger per module: `logging.getLogger(__name__)`.
17. **Read the source file before editing** — check existing patterns, don't assume.
18. **Run `uv run pytest` after changes** — verify nothing is broken before finishing.
