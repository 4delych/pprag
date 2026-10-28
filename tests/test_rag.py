from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from qdrant_client import QdrantClient

from rag_demo import api
from rag_demo.documents import load_chunks
from rag_demo.pipeline import NO_DATA, Rag
from rag_demo.settings import Settings


class FakeModels:
    """A deterministic test double. NOT a semantic embedding or a real LLM."""
    def __init__(self):
        self.answer_calls = 0
        self.last_context = ""
        self.output = "Используйте команду из документа [1]."

    def embed(self, texts):
        return [[1.0, 0.0] if "запуск" in t.lower() else [0.0, 1.0]
                for t in texts]

    def answer(self, question, context):
        self.answer_calls += 1
        self.last_context = context
        return self.output


@pytest.fixture
def rig():
    db = QdrantClient(":memory:")
    model = FakeModels()
    rag = Rag(Settings(_env_file=None, score_threshold=0.8), model, db)
    yield rag, model, db
    db.close()


def doc(text="Запуск: uvicorn app.main:app --port 8000", source="start.md"):
    return Document(page_content=text, metadata={
        "source": source, "title": "TaskBoard", "section": "Запуск", "version": "1.0",
    })


def test_sources_and_context_are_preserved(rig):
    rag, model, _ = rig
    rag.index([doc()])
    result = rag.ask("Запуск проекта")
    assert result["status"] == "generated"
    assert result["sources"][0]["source"] == "start.md"
    assert result["citations"] == [1]
    assert "uvicorn app.main:app" in model.last_context
    assert "версия 1.0" in model.last_context


def test_no_match_does_not_call_generator(rig):
    rag, model, _ = rig
    rag.index([doc()])
    result = rag.ask("SAML")
    assert result["answer"] == NO_DATA
    assert result["sources"] == []
    assert model.answer_calls == 0


@pytest.mark.parametrize("output,status", [
    ("Ответ без ссылки", "citation_warning"),
    ("Ответ [99]", "citation_warning"),
    ("Ответ [1] [99]", "citation_warning"),
    (NO_DATA, "insufficient_evidence"),
])
def test_citation_and_refusal_status(rig, output, status):
    rag, model, _ = rig
    rag.index([doc()])
    model.output = output
    assert rag.ask("Запуск")["status"] == status


def test_reindex_is_idempotent_and_removed_docs_disappear(rig):
    rag, _, db = rig
    first = rag.index([doc(), doc("Запуск второго проекта", "old.md")])
    repeat = rag.index([doc(), doc("Запуск второго проекта", "old.md")])
    assert first == repeat
    assert db.count(first["alias"], exact=True).count == 2
    rag.index([doc()])
    assert db.count(first["alias"], exact=True).count == 1
    assert {s["source"] for s in rag.retrieve("Запуск")} == {"start.md"}


def test_failed_reindex_keeps_previous_snapshot(rig):
    rag, model, _ = rig
    rag.index([doc()])
    original = model.embed
    model.embed = lambda texts: []
    with pytest.raises(ValueError):
        rag.index([doc("Запуск новой версии")])
    model.embed = original
    assert rag.retrieve("Запуск")[0]["text"] == doc().page_content


def test_markdown_headers_size_and_version(tmp_path):
    (tmp_path / "manual.md").write_text("# Проект\n\n## Запуск\n\n" + "Инструкция. " * 90,
                                       encoding="utf-8")
    chunks = load_chunks(tmp_path, "2.0", size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c.page_content) <= 200 for c in chunks)
    assert all(c.metadata["section"] == "Запуск" for c in chunks)
    assert all(c.metadata["source"] == "manual.md" for c in chunks)
    assert all(c.metadata["version"] == "2.0" for c in chunks)


def test_empty_corpus_and_invalid_overlap(tmp_path, rig):
    with pytest.raises(ValueError, match="No Markdown"):
        load_chunks(tmp_path, "1")
    with pytest.raises(ValueError):
        Settings(_env_file=None, chunk_size=100, chunk_overlap=100)
    with pytest.raises(ValueError, match="empty"):
        rig[0].index([])


def test_api_and_input_validation(rig, monkeypatch):
    rag, _, _ = rig
    rag.index([doc()])
    monkeypatch.setattr(api, "get_rag", lambda: rag)
    client = TestClient(api.app)
    assert client.post("/ask", json={"question": "Запуск"}).json()["sources"]
    assert client.post("/ask", json={"question": ""}).status_code == 422
    assert client.post("/ask", json={"question": "  "}).status_code == 422
    assert client.post("/ask", json={"question": "x" * 2001}).status_code == 422


def test_sample_corpus_is_loadable():
    chunks = load_chunks(Path("knowledge"), "1.0")
    assert {c.metadata["source"] for c in chunks} == {
        "getting-started.md", "configuration.md", "troubleshooting.md",
    }
