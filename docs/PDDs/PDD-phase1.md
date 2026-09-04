# Phase 1 Project Design Document — Local AI Platform (As-Built)

**Status:** Complete (retrospective PDD — written after implementation, since none existed)
**Source:** `docs/phase1.md`, `docker-compose.yml`, `Clive_Scope.txt`

## 1. Objective

Stand up a minimal, fully self-hosted local LLM environment as the foundation for every later phase: no cloud AI dependency, Docker-first, reproducible from a single `docker compose up -d`.

## 2. Scope

**In scope (delivered):**
- Local LLM inference via Ollama
- A chat UI via Open WebUI
- GPU-accelerated inference on the development host's RTX 3080

**Out of scope (deferred to later phases):**
- Vector storage / RAG (Phase 2)
- Any external API integration (Phase 3+)
- Reverse proxy / HTTPS (Phase 5)

## 3. Architecture (as implemented)

```
┌─────────────┐        ┌──────────────┐
│  Open WebUI  │◄──────►│    Ollama     │
│  (port 3000) │  HTTP  │ (port 11435,  │
│              │        │  GPU-backed)  │
└─────────────┘        └──────────────┘
```

Both run as Docker Compose services (`clive-webui`, `clive-ollama`), on the same Docker network, with no reverse proxy in front of either yet.

## 4. Key Decisions

| Decision | Choice | Rationale | ADR |
|---|---|---|---|
| Local inference engine | Ollama | Simple Docker deployment, multi-model support, mature ecosystem | `docs/ADR/adr-001-local-llm-stack.md` |
| Chat interface | Open WebUI | Open-source, designed to pair with Ollama, later extensible to RAG (Phase 2) | `docs/ADR/adr-001-local-llm-stack.md` |
| GPU access | Docker Compose `deploy.resources.reservations.devices` (NVIDIA) | Matches the RTX 3080 development host; portable to future Threadripper/RTX 5090 hardware without redesign | — |

## 5. Configuration (as implemented)

`docker-compose.yml` (relevant excerpt):

```yaml
ollama:
  image: ollama/ollama
  container_name: clive-ollama
  ports: ["11435:11434"]
  volumes: ["/data/ollama:/root/.ollama"]
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]

open-webui:
  image: ghcr.io/open-webui/open-webui:main
  container_name: clive-webui
  ports: ["3000:8080"]
  volumes: ["/data/openwebui_data:/app/backend/data"]
```

Note: Ollama's host port is mapped to `11435` (not the default `11434`), and Open WebUI is reachable on `3000`.

## 6. Verification

- `docker compose ps` — both containers running
- `docker exec -it clive-ollama ollama list` — models present after `ollama pull`
- Open WebUI reachable at `http://localhost:3000` and able to chat against a pulled model

## 7. Models in Use

- `llama3.2` — general purpose (~3B params, ~2GB)
- `qwen2.5-coder:7b` — code generation (~7B params, ~4.7GB)
- `nomic-embed-text` — added in Phase 2 for embeddings

## 8. Outcome

A working, GPU-accelerated, fully local chat interface with no cloud dependency, serving as the base layer for Phase 2's RAG upgrade.

## 9. Follow-on Work Identified at the Time

- No production-grade vector storage (addressed in Phase 2)
- No enterprise document indexing (addressed in Phase 2)
- No external API integration (addressed in Phase 3)
