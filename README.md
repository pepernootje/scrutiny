# Scrutiny

A Streamlit-based experimentation environment for designing, evaluating, and refining
**supervisory checks** — rules that detect and classify specific disclosures in public
prospectus documents.

## Overview

A supervisory check is a pipeline of three sequential steps:

1. **Chunking** — splitting document text into candidate spans
2. **Detection** — filtering chunks using regex or Azure AI Search
3. **Classification** — evaluating chunks against an LLM prompt template

## Quick Start

```shell
git clone <azure_url>
cd scrutiny
uv sync --extra dev
uv run pre-commit install

# Run the Streamlit app in dev mode (no Azure credentials needed)
PLAYGROUND_ENV=development uv run streamlit run src/scrutiny/app/Home.py
```

## Run Modes

| Mode | Activates when | Usage |
|---|---|---|
| Production | `PLAYGROUND_ENV=production` + Azure creds | Live deployment |
| Development | `PLAYGROUND_ENV=development` (default) | Local dev and CI |
| UX Demo | `demo_mode` sidebar toggle | Analysts evaluating UI |

## Testing

```shell
uv run pytest
uv run pytest --cov=src  # with coverage
```

## Documentation

```shell
uv sync --extra docs
uv run mkdocs serve
```

## Project Structure

```
scrutiny/
├── src/scrutiny/
│   ├── models.py           # Data models
│   ├── config.py           # Runtime configuration
│   ├── adapters/           # Search and classification adapters
│   ├── chunking/           # Document chunking
│   ├── detection/          # Chunk detection
│   ├── classification/     # LLM classification
│   └── app/                # Streamlit application
├── tests/                  # Test suite
├── configs/                # Check configuration YAML files
└── docs/                   # Documentation
```
