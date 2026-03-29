import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Optional cloud keys (not required when using Ollama)
    grok_api_key: str = os.getenv("GROK_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    # Business rules
    high_value_threshold: float = float(os.getenv("HIGH_VALUE_THRESHOLD", "10000"))

    # DB
    db_path: str = os.getenv("DB_PATH", "data/inventory.db")

settings = Settings()
