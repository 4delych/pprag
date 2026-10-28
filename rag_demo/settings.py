from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_url: str = "http://localhost:11434"
    embed_model: str = "bge-m3"
    chat_model: str = "qwen2.5:3b"
    qdrant_url: str = "http://localhost:6333"
    qdrant_path: str = ""
    collection: str = "project_docs"
    docs_version: str = "1.0"
    chunk_size: int = Field(900, ge=100)
    chunk_overlap: int = Field(150, ge=0)
    top_k: int = Field(4, ge=1, le=10)
    score_threshold: float = Field(0.35, ge=-1, le=1)

    @model_validator(mode="after")
    def validate_overlap(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self
