from pathlib import Path

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


def load_chunks(root: Path, version: str, size=900, overlap=150):
    """Read UTF-8 Markdown, keep headings and relative source paths."""
    headers = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "title"), ("##", "section"), ("###", "subsection")],
        strip_headers=False,
    )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap,
    )
    chunks = []
    for path in sorted(root.rglob("*.md")):
        sections = headers.split_text(path.read_text(encoding="utf-8-sig"))
        for chunk in splitter.split_documents(sections):
            chunk.metadata.update(
                source=path.relative_to(root).as_posix(), version=version,
            )
            chunks.append(chunk)
    if not chunks:
        raise ValueError(f"No Markdown documents in {root}")
    return chunks
