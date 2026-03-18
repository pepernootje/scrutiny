# About Scrutiny

Scrutiny is an internal analyst tool for iterative testing and side-by-side comparison
of supervisory check behaviour on prospectus documents.

It is **not** a production service — it is an analyst tool that reuses the same modules
as production (`chunking/`, `detection/`, `classification/`).

## Architecture

The application uses Azure services in production:

- **Azure AI Search** for semantic chunk detection
- **Azure OpenAI** for LLM-based classification

Both services have stub implementations that allow the tool to run fully offline,
without any Azure credentials.

## Run Modes

| Mode | Environment Variable | Description |
|---|---|---|
| Production | `PLAYGROUND_ENV=production` | Uses real Azure services |
| Development | `PLAYGROUND_ENV=development` | Uses stub implementations |
| UX Demo | Sidebar toggle | Simulated results for demos |
