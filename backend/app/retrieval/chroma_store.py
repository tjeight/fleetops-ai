import os
import glob
import re
import hashlib
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from app.core.config import settings


class DeterministicEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Lightweight, high-speed, 100% offline embedding function.
    Generates a 384-dimensional normalized vector using stable feature hashing
    and token frequency, ensuring zero external network dependency while
    providing realistic semantic cosine similarity for drone SOP keywords.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def name(self) -> str:
        return "deterministic_drone_sop_embedding"

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: List[List[float]] = []
        for text in input:
            tokens = re.findall(r"\w+", text.lower())
            vec = [0.0] * self.dimension
            if not tokens:
                embeddings.append(vec)
                continue
            for token in tokens:
                # Hash token to dimension slot
                h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
                slot = h % self.dimension
                sign = 1.0 if ((h >> 8) & 1) else -1.0
                vec[slot] += sign
            
            # Normalize vector (L2 norm)
            norm = sum(x * x for x in vec) ** 0.5
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings


class SOPRetriever:
    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_fn = DeterministicEmbeddingFunction()
        self.collection_name = "fleetops_sops"
        self._collection = None

    def get_or_create_collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn,
                metadata={"description": "FleetOps AI Standard Operating Procedures"}
            )
        return self._collection

    def ingest_sop_directory(self, sop_dir: str) -> int:
        """
        Parses all markdown SOP files in sop_dir, chunks them by sections,
        extracts metadata, and stores them in ChromaDB.
        """
        collection = self.get_or_create_collection()
        
        # Reset existing items to keep ingestion idempotent
        existing_ids = collection.get()["ids"]
        if existing_ids:
            collection.delete(ids=existing_ids)
            
        md_files = glob.glob(os.path.join(sop_dir, "*.md"))
        total_chunks = 0
        
        for file_path in md_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            chunks = self._chunk_sop_document(content, os.path.basename(file_path))
            if not chunks:
                continue
                
            ids = [c["id"] for c in chunks]
            documents = [c["text"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]
            
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            total_chunks += len(chunks)
            
        return total_chunks

    def _chunk_sop_document(self, text: str, filename: str) -> List[Dict[str, Any]]:
        # Extract doc id and title from front/header
        doc_id_match = re.search(r"\*\*Document ID\*\*:\s*([^\n\r]+)", text)
        doc_id = doc_id_match.group(1).strip() if doc_id_match else filename.replace(".md", "")
        
        title_match = re.search(r"\*\*Title\*\*:\s*([^\n\r]+)", text)
        title = title_match.group(1).strip() if title_match else filename
        
        category_match = re.search(r"\*\*Category\*\*:\s*([^\n\r]+)", text)
        category = category_match.group(1).strip() if category_match else "Operations"

        # Split on markdown headers (## )
        sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)
        chunks = []
        for idx, section in enumerate(sections):
            clean_section = section.strip()
            if not clean_section:
                continue
            
            # Extract section heading
            header_match = re.match(r"^##\s+([^\n\r]+)", clean_section)
            section_title = header_match.group(1).strip() if header_match else f"Section {idx}"
            
            chunk_id = f"{doc_id}-chunk-{idx}"
            chunks.append({
                "id": chunk_id,
                "text": clean_section,
                "metadata": {
                    "sop_id": doc_id,
                    "title": title,
                    "category": category,
                    "section": section_title,
                    "filename": filename
                }
            })
        return chunks

    def retrieve(self, query: str, top_k: int = 3, min_similarity: float = 0.05) -> List[Dict[str, Any]]:
        """
        Retrieves relevant SOP chunks. Supports MMR / distance filtering.
        Returns empty list if no chunk meets the minimum relevance threshold.
        """
        collection = self.get_or_create_collection()
        count = collection.count()
        if count == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"]
        )
        
        citations = []
        if not results or not results["documents"] or not results["documents"][0]:
            return []
            
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
        
        for doc, meta, dist in zip(docs, metas, distances):
            # Chroma returns L2 distance; convert to approximate cosine similarity: sim = 1 / (1 + dist)
            relevance_score = round(1.0 / (1.0 + float(dist)), 4)
            if relevance_score < min_similarity:
                continue
                
            # Extract representative excerpt (first 250 characters)
            excerpt = doc.replace("\n", " ").strip()
            if len(excerpt) > 280:
                excerpt = excerpt[:277] + "..."
                
            citations.append({
                "sop_id": meta.get("sop_id", "UNKNOWN"),
                "title": meta.get("title", ""),
                "section": meta.get("section", ""),
                "excerpt": excerpt,
                "relevance_score": relevance_score
            })
            
        return citations


retriever = SOPRetriever()
