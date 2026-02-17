import json
import os
import asyncio
from typing import List, Dict, Optional
import structlog
from ..core.interfaces import MemoryInterface
from ..core.types import MemoryObject
from ..infra.database import db
from ..infra.models import MemoryLogModel
from sqlalchemy.future import select
import numpy as np

logger = structlog.get_logger()

class HybridMemory(MemoryInterface):
    """
    Production-grade memory system combining:
    1. Short-term vector search (In-memory/Local Persisted)
    2. Long-term episodic storage (SQL Database)
    """
    def __init__(self, persist_path: str = "./vector_store.json"):
        self.persist_path = persist_path
        self.vectors: Dict[str, List[float]] = {}
        self.documents: Dict[str, MemoryObject] = {}
        self.logger = logger.bind(component="HybridMemory")
        self._load_local_vectors()

    def _load_local_vectors(self):
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, "r") as f:
                    data = json.load(f)
                    for item_data in data:
                        obj = MemoryObject(**item_data)
                        self.documents[str(obj.id)] = obj
                        if obj.vector:
                            self.vectors[str(obj.id)] = obj.vector
                self.logger.info("Loaded persisted vectors", count=len(self.documents))
            except Exception as e:
                self.logger.error("Failed to load vector store", error=str(e))

    async def _persist_local_vectors(self):
        # In a real system, this is Qdrant/Milvus, so no manual file save needed.
        # For this file-based hybrid approach:
        try:
            data = [doc.model_dump(mode='json') for doc in self.documents.values()]
            # Run in thread to avoid blocking loop
            await asyncio.to_thread(self._write_file, data)
        except Exception as e:
            self.logger.error("Failed to persist vectors", error=str(e))

    def _write_file(self, data):
        with open(self.persist_path, "w") as f:
            json.dump(data, f)

    async def store(self, item: MemoryObject, collection: str = "default") -> bool:
        # 1. Store in Vector Memory (Short-term context)
        self.documents[str(item.id)] = item
        if item.vector:
            self.vectors[str(item.id)] = item.vector

        await self._persist_local_vectors()

        # 2. Store in Episodic Database (Long-term audit)
        try:
            async for session in db.get_session():
                log = MemoryLogModel(
                    id=str(item.id),
                    agent_id=item.metadata.get("role"), # Mapping role as ID for MVP simplicity
                    content=item.content,
                    vector_id=str(item.id),
                    metadata_info=item.metadata,
                    timestamp=item.timestamp
                )
                session.add(log)
                await session.commit()
                self.logger.debug("Persisted to SQL", id=str(item.id))
        except Exception as e:
            self.logger.error("SQL Persistence Failed", error=str(e))

        return True

    async def retrieve(self, query: str, limit: int = 5, collection: str = "default") -> List[MemoryObject]:
        # Basic fallback: return recent items if no vector (should be handled by search_by_vector mostly)
        # But here we implement a "recent" retrieval if query is just text without embedding
        # Ideally, caller embeds query and calls search_by_vector
        items = list(self.documents.values())
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items[:limit]

    async def search_by_vector(self, vector: List[float], limit: int = 5, collection: str = "default") -> List[MemoryObject]:
        if not self.vectors:
            return []

        # Convert to numpy for speed
        ids = list(self.vectors.keys())
        matrix = np.array([self.vectors[i] for i in ids])
        query_vec = np.array(vector)

        if matrix.shape[0] == 0:
            return []

        # Cosine Similarity
        norm_matrix = np.linalg.norm(matrix, axis=1)
        norm_query = np.linalg.norm(query_vec)

        if norm_query == 0:
             return []

        similarities = np.dot(matrix, query_vec) / (norm_matrix * norm_query)

        # Top K
        top_k_indices = np.argsort(similarities)[-limit:][::-1]

        results = []
        for idx in top_k_indices:
            mem_id = ids[idx]
            results.append(self.documents[mem_id])

        return results

    async def clear(self, collection: str = "default"):
        self.vectors = {}
        self.documents = {}
        if os.path.exists(self.persist_path):
            os.remove(self.persist_path)
