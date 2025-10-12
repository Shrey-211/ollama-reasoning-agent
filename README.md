# ollama-reasoning-agent

Ollama-based local reasoning agent (OOP). Docker-ready. Includes:

- Ollama client wrapper (mock if not installed)
- Sentiment analyzer (transformers fallback)
- TF-IDF DocumentStore
- Structured JSON intent parsing + tool execution
- Unit tests (pytest)

## Quickstart (Docker)

1. Copy `.env.example` to `.env` and adjust values.
2. Build and run with Docker Compose:

```bash
make docker-build
make docker-up
```

3. Open container logs or attach to the CLI service to interact.

## Project structure

```
ollama-reasoning-agent/
├─ README.md
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
├─ Makefile
├─ src/
│  ├─ __init__.py
│  ├─ ollama_client.py
│  ├─ sentiment.py
│  ├─ document_store.py
│  ├─ tools.py
│  ├─ agent.py
│  └─ main.py
└─ tests/
   └─ test_agent.py
```

