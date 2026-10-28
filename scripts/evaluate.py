"""Run the real configured models; save evidence rather than canned answers."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_demo.models import OllamaModels
from rag_demo.pipeline import NO_DATA, Rag
from rag_demo.settings import Settings


def main():
    settings = Settings()
    rag = Rag(settings, OllamaModels(settings))
    cases = json.loads(Path("evaluation/questions.json").read_text(encoding="utf-8"))
    results = []
    try:
        for case in cases:
            response = rag.ask(case["question"])
            found = any(
                s["source"] == case.get("expected_source")
                and s.get("section") == case.get("expected_section")
                for s in response["sources"]
            ) if case["answerable"] else None
            results.append({
                **case, **response, "expected_chunk_in_top_k": found,
                "refused": NO_DATA in response["answer"],
                "facts_present": {fact: fact in response["answer"]
                                  for fact in case.get("facts", [])},
            })
    finally:
        rag.db.close()
    output = Path("artifacts/runs")
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "backend": "real Ollama", "embed_model": settings.embed_model,
        "chat_model": settings.chat_model, "top_k": settings.top_k,
        "score_threshold": settings.score_threshold,
        "note": "String matches are an aid, not a semantic correctness metric.",
        "results": results,
    }
    destination = output / f"evaluation-{stamp}.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
