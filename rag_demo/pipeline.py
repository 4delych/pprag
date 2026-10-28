import hashlib
import re
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from .settings import Settings

NO_DATA = "В документации нет достаточной информации для ответа."


class Rag:
    def __init__(self, settings: Settings, model, database=None):
        self.settings = settings
        self.model = model
        self.db = database if database is not None else (
            QdrantClient(path=settings.qdrant_path) if settings.qdrant_path
            else QdrantClient(url=settings.qdrant_url, timeout=30)
        )

    def index(self, chunks) -> dict:
        if not chunks:
            raise ValueError("Cannot index an empty document set")
        # A content/config fingerprint gives each snapshot its own collection.
        # Re-indexing the same data is an upsert; changed data gets a new snapshot.
        fingerprint = hashlib.sha256(repr([
            self.settings.embed_model,
            [(c.page_content, c.metadata) for c in chunks],
        ]).encode()).hexdigest()[:16]
        snapshot = f"{self.settings.collection}_{fingerprint}"
        for start in range(0, len(chunks), 16):
            batch = chunks[start:start + 16]
            vectors = self.model.embed([c.page_content for c in batch])
            if len(vectors) != len(batch) or not vectors:
                raise ValueError("Embedding provider returned an incomplete batch")
            if not self.db.collection_exists(snapshot):
                self.db.create_collection(
                    collection_name=snapshot,
                    vectors_config=models.VectorParams(
                        size=len(vectors[0]), distance=models.Distance.COSINE,
                    ),
                )
            self.db.upsert(
                collection_name=snapshot,
                points=[models.PointStruct(
                    id=str(uuid5(NAMESPACE_URL, f"{snapshot}/{start + i}")),
                    vector=vector,
                    payload={"text": chunk.page_content, **chunk.metadata},
                ) for i, (chunk, vector) in enumerate(zip(batch, vectors, strict=True))],
                wait=True,
            )
        alias = self.settings.collection
        aliases = {a.alias_name for a in self.db.get_aliases().aliases}
        changes = []
        if alias in aliases:
            changes.append(models.DeleteAliasOperation(
                delete_alias=models.DeleteAlias(alias_name=alias),
            ))
        changes.append(models.CreateAliasOperation(create_alias=models.CreateAlias(
            alias_name=alias, collection_name=snapshot,
        )))
        self.db.update_collection_aliases(change_aliases_operations=changes)
        return {"collection": snapshot, "chunks": len(chunks), "alias": alias}

    def retrieve(self, question: str) -> list[dict]:
        vector = self.model.embed([question])[0]
        hits = self.db.query_points(
            collection_name=self.settings.collection,
            query=vector, limit=self.settings.top_k,
            score_threshold=self.settings.score_threshold,
            with_payload=True,
        ).points
        return [dict(id=i, score=round(hit.score, 4), **hit.payload)
                for i, hit in enumerate(hits, start=1)]

    def ask(self, question: str) -> dict:
        sources = self.retrieve(question)
        if not sources:
            return {"answer": NO_DATA, "sources": [], "citations": [],
                    "status": "no_context"}
        context = "\n\n".join(
            f"[{s['id']}] {s['source']} | {s.get('section', s.get('title', ''))} "
            f"| версия {s['version']}\n{s['text']}" for s in sources
        )
        answer = self.model.answer(question, context)
        valid_ids = {s["id"] for s in sources}
        cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
        # This checks reference IDs, not whether the source proves the claim.
        if NO_DATA in answer:
            status = "insufficient_evidence"
        elif not cited or not cited.issubset(valid_ids):
            status = "citation_warning"
        else:
            status = "generated"
        return {"answer": answer, "sources": sources,
                "citations": sorted(cited & valid_ids), "status": status}
