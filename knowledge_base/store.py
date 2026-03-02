import chromadb
from typing import Optional

class KnowledgeBase:
    def __init__(self, persist_dir: str = "./knowledge_base/chroma_db"):
        if persist_dir == ":memory:":
            self._client = chromadb.Client()
        else:
            self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name="it_guides",
            metadata={"hnsw:space": "cosine"},
        )

    def add_document(self, doc_id: str, content: str, metadata: Optional[dict] = None) -> None:
        self._collection.upsert(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata or {"source": doc_id}],
        )

    def search(self, query: str, top_k: int = 3, min_confidence: float = 0.0) -> list[dict]:
        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, max(1, self._collection.count())),
        )
        if not results["documents"] or not results["documents"][0]:
            return []
        output = []
        for i, doc in enumerate(results["documents"][0]):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite. Convert to confidence.
            distance = results["distances"][0][i]
            confidence = 1.0 - (distance / 2.0)
            if confidence >= min_confidence:
                output.append({
                    "content": doc,
                    "source": results["metadatas"][0][i].get("source", "unknown"),
                    "confidence": round(confidence, 4),
                })
        return sorted(output, key=lambda x: x["confidence"], reverse=True)

    def count(self) -> int:
        return self._collection.count()
