#!/usr/bin/env python3
"""
CLI to load/reload IT guides from Markdown files into ChromaDB.
Usage: python -m knowledge_base.loader
"""
from pathlib import Path
from knowledge_base.store import KnowledgeBase

GUIDES_DIR = Path(__file__).parent / "guides"

def load_all_guides(persist_dir: str = "./knowledge_base/chroma_db") -> int:
    kb = KnowledgeBase(persist_dir=persist_dir)
    count = 0
    for md_file in GUIDES_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_id = md_file.stem
        kb.add_document(doc_id=doc_id, content=content, metadata={"source": md_file.name})
        print(f"  Loaded: {md_file.name}")
        count += 1
    print(f"\nTotal guides loaded: {count}")
    return count

if __name__ == "__main__":
    print("Loading IT guides into ChromaDB...")
    load_all_guides()
    print("Done.")
