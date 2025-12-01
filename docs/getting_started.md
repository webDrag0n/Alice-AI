# Getting Started

This guide will help you set up and run the Alice AI Agent on your local machine.

## Prerequisites

- **Docker & Docker Compose**: Essential for running the backend, database, and frontend services.
- **Node.js (v18+)**: Required if you plan to run the Minecraft Agent or develop the frontend locally without Docker.
- **Python (3.10+)**: Required for local backend development.

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/alice-ai.git
   cd alice-ai/alice_dev
   ```

2. **Environment Configuration**
   The project uses `docker-compose.yml` for configuration. You can also create a `.env` file in `alice_dev/docker/` if needed, but default settings usually work for local testing.

## LLM Configuration

Alice AI requires a Large Language Model (LLM) to function. You have two primary options:

### Option 1: Local Ollama (Recommended for Privacy/Cost)
By default, the system is configured to connect to an Ollama instance running on your host machine.

1. **Install Ollama**: [https://ollama.com/](https://ollama.com/)
2. **Pull the Model**:
   ```bash
   ollama pull qwen2.5:14b
   # You can also pull a smaller model for perception
   ollama pull qwen2.5:0.5b
   ```
3. **Configuration**:
   Ensure your `docker/docker-compose.yml` points to the correct host address (usually `http://host.docker.internal:11434`).

### Option 2: OpenAI-Compatible API (DeepSeek, OpenAI, etc.)
To use a cloud provider, modify the environment variables in `docker/docker-compose.yml` or `config/settings.py`.

```yaml
environment:
  - LLM_PROVIDER=openai
  - OPENAI_BASE_URL=https://api.deepseek.com/v1
  - OPENAI_API_KEY=your-api-key
  - OPENAI_MODEL_MAIN=deepseek-chat
  - OPENAI_MODEL_REASONING=deepseek-reasoner
```

## Running the Project

The easiest way to run the full stack (Backend, Frontend, Weaviate) is via Docker Compose.

1. **Navigate to the docker directory**:
   ```bash
   cd docker
   ```

2. **Start the services**:
   ```bash
   # Build and start in detached mode
   docker-compose up --build -d
   ```

3. **Access the Application**:
   - **Frontend**: Open [http://localhost:5173](http://localhost:5173) in your browser.
   - **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Stopping the Project

```bash
docker-compose down
# To remove volumes (reset memory):
docker-compose down -v
```

## Troubleshooting

- **LLM Connection Error**: Ensure Ollama is running and accessible. If on Linux, you might need to use the host IP instead of `host.docker.internal`.
- **Weaviate Error**: Wait a few seconds for the database to initialize on the first run.
