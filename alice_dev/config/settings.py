import os
import json
from pathlib import Path

# =========================================================================
# Module Level Config Loading
# =========================================================================
# Load from llm.json if available, otherwise use env vars or defaults
_llm_config = {}
try:
    config_path = Path(__file__).parent / "llm.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            _llm_config = json.load(f)
            print(f"Loaded LLM config from {config_path}")
except Exception as e:
    print(f"Failed to load llm.json: {e}")

def _get_conf(key, default):
    """Helper to get config value with priority: Env Var > JSON Config > Default"""
    return os.getenv(key, _llm_config.get(key, default))


class Settings:
    # =========================================================================
    # 1. Base Configuration
    # =========================================================================
    LOG_DIR = os.getenv("LOG_DIR", "/logs")
    LOG_DIR_BACKEND = os.path.join(LOG_DIR, "backend")
    
    # =========================================================================
    # 2. LLM Provider Configuration
    # =========================================================================
    
    # LLM_PROVIDER: 'ollama' or 'openai'
    LLM_PROVIDER = _get_conf("LLM_PROVIDER", "ollama")

    # --- Ollama Settings (Default) ---
    OLLAMA_BASE_URL = _get_conf("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_API_KEY = _get_conf("OLLAMA_API_KEY", "mock-key")
    OLLAMA_MODEL_MAIN = _get_conf("OLLAMA_MODEL_MAIN", "ollama/qwen3:14b")
    OLLAMA_MODEL_PERCEPTION = _get_conf("OLLAMA_MODEL_PERCEPTION", "ollama/qwen3:4b")

    # --- OpenAI Proxy Settings (DeepSeek, SiliconFlow, etc.) ---
    OPENAI_BASE_URL = _get_conf("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    OPENAI_API_KEY = _get_conf("OPENAI_API_KEY", "")
    OPENAI_MODEL_MAIN = _get_conf("OPENAI_MODEL_MAIN", "deepseek-chat")
    OPENAI_MODEL_REASONING = _get_conf("OPENAI_MODEL_REASONING", "deepseek-reasoner")
    OPENAI_MODEL_PERCEPTION = _get_conf("OPENAI_MODEL_PERCEPTION", "deepseek-chat")
    
    # --- Vectorizer Settings ---
    VECTORIZER_PROVIDER = _get_conf("VECTORIZER_PROVIDER", "ollama")
    OLLAMA_EMBEDDING_MODEL = _get_conf("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    OPENAI_EMBEDDING_MODEL = _get_conf("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # =========================================================================
    # 3. Active Model Selection
    # =========================================================================
    @property
    def LLM_API_BASE(self):
        if self.LLM_PROVIDER == "openai":
            return self.OPENAI_BASE_URL
        # For Docker, we might need host.docker.internal, but for local defaults we use localhost.
        # The docker-compose.yml should override OLLAMA_BASE_URL to host.docker.internal.
        return self.OLLAMA_BASE_URL

    @property
    def LLM_API_KEY(self):
        if self.LLM_PROVIDER == "openai":
            return self.OPENAI_API_KEY
        return self.OLLAMA_API_KEY

    @property
    def LLM_MODEL(self):
        if self.LLM_PROVIDER == "openai":
            return self.OPENAI_MODEL_MAIN
        return self.OLLAMA_MODEL_MAIN

    @property
    def THINKING_MODEL(self):
        # Allows overriding thinking model specifically
        if self.LLM_PROVIDER == "openai":
            return os.getenv("THINKING_MODEL", self.OPENAI_MODEL_REASONING)
        return os.getenv("THINKING_MODEL", self.LLM_MODEL)

    @property
    def PERCEPTION_MODEL(self):
        if self.LLM_PROVIDER == "openai":
            return os.getenv("PERCEPTION_MODEL", self.OPENAI_MODEL_PERCEPTION)
        return os.getenv("PERCEPTION_MODEL", self.OLLAMA_MODEL_PERCEPTION)

    @property
    def PERCEPTION_API_BASE(self):
        # Allow specific override for perception API, otherwise follow provider
        return os.getenv("PERCEPTION_API_BASE", self.LLM_API_BASE)

    @property
    def PERCEPTION_API_KEY(self):
        return os.getenv("PERCEPTION_API_KEY", self.LLM_API_KEY)

    # =========================================================================
    # 4. Model Parameters
    # =========================================================================
    THINK_MODEL_PARAMS = {
        "temperature": float(os.getenv("THINK_TEMPERATURE", "0.7")),
        "top_p": float(os.getenv("THINK_TOP_P", "0.9")), # Adjusted for OpenAI compatibility (usually < 1.0)
        "max_tokens": int(os.getenv("THINK_MAX_TOKENS", "8192")),
        "presence_penalty": float(os.getenv("THINK_PRESENCE_PENALTY", "0.0")),
        "frequency_penalty": float(os.getenv("THINK_FREQUENCY_PENALTY", "0.0")),
        "seed": int(os.getenv("THINK_SEED", "230")) if os.getenv("THINK_SEED") else None, # OpenAI seed support varies
    }
    
    PERCEPTION_MODEL_PARAMS = {
        "temperature": float(os.getenv("PERCEPTION_TEMPERATURE", "0.3")),
        "top_p": float(os.getenv("PERCEPTION_TOP_P", "0.8")),
        "max_tokens": int(os.getenv("PERCEPTION_MAX_TOKENS", "2048")),
        "seed": int(os.getenv("PERCEPTION_SEED", "42")) if os.getenv("PERCEPTION_SEED") else None,
    }
    
    # =========================================================================
    # 5. System Settings
    # =========================================================================
    INSTANT_MEMORY_LIMIT = int(os.getenv("INSTANT_MEMORY_LIMIT", "13"))
    WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")
    WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT", "8080"))
    WEAVIATE_GRPC_HOST = os.getenv("WEAVIATE_GRPC_HOST", "localhost")
    WEAVIATE_GRPC_PORT = int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))

    AGENT_NAME = "Alice"
    THINKING_INTERVAL = float(os.getenv("THINKING_INTERVAL", "0.1"))
    CONTINUOUS_THINKING = os.getenv("CONTINUOUS_THINKING", "false").lower() == "true"

    # =========================================================================
    # 6. Vector Database Settings
    # =========================================================================
    # (Moved to Section 2 to use _get_conf)
    # VECTORIZER_PROVIDER = ...
    # OLLAMA_EMBEDDING_MODEL = ...
    # OPENAI_EMBEDDING_MODEL = ...

    # =========================================================================
    # 7. Logging Configuration
    # =========================================================================
    ENABLE_LLM_LOGS = os.getenv("ENABLE_LLM_LOGS", "false").lower() == "true"

settings = Settings()
