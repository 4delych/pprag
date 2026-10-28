from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .models import OllamaModels
from .pipeline import Rag
from .settings import Settings


@lru_cache
def get_rag():
    settings = Settings()
    return Rag(settings, OllamaModels(settings))


@asynccontextmanager
async def lifespan(app):
    yield
    if get_rag.cache_info().currsize:
        get_rag().db.close()
        get_rag.cache_clear()


app = FastAPI(title="Помощник по документации", lifespan=lifespan)


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@app.post("/ask")
def ask(body: Question):
    if not body.question.strip():
        raise HTTPException(422, "Вопрос не должен быть пустым")
    try:
        return get_rag().ask(body.question.strip())
    except Exception as exc:
        # Log details locally; do not expose server/provider internals to clients.
        import logging
        logging.getLogger(__name__).exception("RAG request failed")
        raise HTTPException(503, "Проверьте Ollama, Qdrant и индексацию документов") from exc
