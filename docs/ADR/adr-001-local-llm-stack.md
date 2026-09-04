# ADR-001: Self-Hosted Local LLM Stack (Ollama + Open WebUI)

## Status
Accepted (implemented, Phase 1)

## Context
CLIVE requires local LLM inference with zero cloud dependency, per the project's "Open Source First / Self Hosted" principle. The stack needed to be Docker-first, GPU-capable on the development host (RTX 3080), and extensible toward RAG in the next phase.

## Decision
Use **Ollama** as the local inference engine and **Open WebUI** as the chat interface, both deployed as Docker Compose services on the same network.

- Ollama: `ollama/ollama` image, GPU reserved via Compose's `deploy.resources.reservations.devices` (NVIDIA), host port `11435`.
- Open WebUI: `ghcr.io/open-webui/open-webui:main` image, host port `3000`, configured to talk to Ollama over the internal Docker network (`OLLAMA_BASE_URL=http://ollama:11434`).

## Alternatives Considered
- **Cloud LLM APIs (OpenAI, Anthropic, etc.)** — rejected: violates the project's no-cloud-AI-without-approval principle and would put company data off-premises.
- **text-generation-webui or LM Studio** in place of Ollama — not chosen; Ollama's simpler Docker deployment and multi-model management were preferred for a single-developer, multi-month project.
- **A custom Gradio/Streamlit chat UI** in place of Open WebUI — rejected; Open WebUI already supports the RAG features (PGVector, Tika, Hybrid Search) needed in Phase 2, avoiding a rewrite.

## Consequences
- Positive: zero cloud dependency, fast local iteration, GPU acceleration on existing hardware, direct upgrade path to RAG without swapping the chat UI.
- Negative: Open WebUI's default vector store and extraction are not production-grade — this was accepted as a known limitation, resolved in Phase 2.
- The chosen images (`ollama/ollama`, `ghcr.io/open-webui/open-webui:main`) both track `latest`/`main` tags rather than pinned versions, which is a reproducibility trade-off worth revisiting (see `docs/known-issues.md`).
