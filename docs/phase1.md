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