from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # GitHub
    github_token: str = ""
    github_api_base: str = "https://api.github.com"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # App
    backend_port: int = 8000
    upload_dir: str = str(Path(__file__).resolve().parent.parent / "uploads")
    max_file_size_mb: int = 10

    # CORS
    allowed_origins: str = "http://localhost:3000,http://13.48.209.41:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
