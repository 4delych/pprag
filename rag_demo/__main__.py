import argparse
import json
from pathlib import Path

from .documents import load_chunks
from .models import OllamaModels
from .pipeline import Rag
from .settings import Settings


def main():
    parser = argparse.ArgumentParser(description="Documentation RAG")
    commands = parser.add_subparsers(dest="command", required=True)
    index = commands.add_parser("index")
    index.add_argument("directory", nargs="?", default="knowledge")
    for name in ("ask", "search"):
        commands.add_parser(name).add_argument("question")
    args = parser.parse_args()
    settings = Settings()
    rag = Rag(settings, OllamaModels(settings))
    try:
        if args.command == "index":
            chunks = load_chunks(Path(args.directory), settings.docs_version,
                                 settings.chunk_size, settings.chunk_overlap)
            result = rag.index(chunks)
        elif args.command == "search":
            result = rag.retrieve(args.question)
        else:
            result = rag.ask(args.question)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        rag.db.close()


if __name__ == "__main__":
    main()
