# Alice AI Agent

This is the development repository for the Alice AI Agent.

## Structure

- `frontend/`: React + Vite application.
- `backend/`: FastAPI server.
- `soul/`: Agent cognitive logic (LangGraph).
- `memory/`: Storage logic (Weaviate).
- `docs/`: Project documentation.
- `docker/`: Docker composition files.

## Getting Started

See `docs/` for detailed architecture and design.

### LLM Configuration

The agent supports both local Ollama models and OpenAI-compatible proxies (e.g., DeepSeek, SiliconFlow).

#### Option 1: Local Ollama (Default)
By default, the system expects Ollama running on the host machine.
- **API Base**: `http://host.docker.internal:11434`
- **Model**: `ollama/qwen3:14b` (Configurable via `LLM_MODEL`)

#### Option 2: OpenAI Proxy
To use an external provider, update `docker/docker-compose.yml` environment variables or modify `config/settings.py`:

```yaml
environment:
  # Switch provider to 'openai'
  - LLM_PROVIDER=openai
  
  # Configure OpenAI Proxy settings
  - OPENAI_BASE_URL=https://api.deepseek.com/v1
  - OPENAI_API_KEY=your-api-key
  - OPENAI_MODEL_MAIN=openai/deepseek-chat
  - OPENAI_MODEL_REASONING=openai/deepseek-reasoner
  
  # Optional: Override specific models if needed
  # - PERCEPTION_MODEL=ollama/qwen3:4b
```

## Running the Project

```bash
docker-compose down -v
docker-compose up --build
docker-compose up -d
```