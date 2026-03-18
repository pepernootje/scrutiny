# Scrutiny

Welcome to the Scrutiny documentation.

Scrutiny is a Streamlit-based experimentation environment for power-users to design,
evaluate, and refine **supervisory checks** — rules that detect and classify specific
disclosures in public prospectus documents.

## Pipeline

A supervisory check is a pipeline of three sequential, independently configurable steps:

1. **Chunking** — splitting document text into candidate spans
2. **Detection** — filtering chunks using regex, Azure AI Search, or hybrid
3. **Classification** — evaluating chunks against an LLM prompt template

## Quick Start

See the [README](https://github.com/scrutiny/scrutiny) for setup instructions.

## API Reference

- [Models](reference/models.md)
- [Config](reference/config.md)
- [Adapters](reference/adapters.md)
- [Chunking](reference/chunking.md)
- [Detection](reference/detection.md)
- [Classification](reference/classification.md)
