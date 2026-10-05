> Historical record as of 2026-08-06, commit 7f6f52d. Not maintained.

# AI Platform - Phase 1: Local LLM Development Environment

A self-hosted AI chat platform running Ollama + Open WebUI via Docker Compose.

## Quick Start

```bash
# Start services
docker compose up -d

# Pull a model
docker exec -it ollama ollama pull llama3.2

# Open the chat UI
# Visit http://localhost:3000
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Ollama | 11434 | LLM inference engine |
| Open WebUI | 3000 | Chat interface |

## Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Check status
docker compose ps

# Pull a new model
docker exec -it ollama ollama pull <model-name>

# List models
docker exec -it ollama ollama list
```

## Models

- `llama3.2` - General purpose (3B, ~2GB)
- `qwen2.5-coder:7b` - Code generation (7B, ~4.7GB)

> **Correction (2026-10-05):** The `docker exec -it ollama ...` commands above
> fail, because the container is named `clive-ollama` (`container_name` in
> `docker-compose.yml`). Use `docker exec -it clive-ollama ...` instead, for
> example `docker exec -it clive-ollama ollama list`.
