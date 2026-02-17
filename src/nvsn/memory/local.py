from ..core.interfaces import MemoryInterface
from ..core.types import MemoryObject
from typing import List, Dict
import numpy as np
import uuid
from datetime import datetime

class LocalVectorMemory(MemoryInterface):
    """
    A simple in-memory vector database implementation using NumPy for cosine similarity.
    Suitable for MVP and testing. Not for large-scale production.
    """
    def __init__(self, embedding_dim: int = 1536):
        self.embedding_dim = embedding_dim
        # Structure: {collection_name: {id: MemoryObject}}
        self.storage: Dict[str, Dict[uuid.UUID, MemoryObject]] = {}
        # Structure: {collection_name: np.array([vector1, vector2, ...])}
        self.vectors: Dict[str, np.ndarray] = {}
        # Structure: {collection_name: [id1, id2, ...]} mapping row index to ID
        self.index_map: Dict[str, List[uuid.UUID]] = {}

    async def store(self, item: MemoryObject, collection: str = "default") -> bool:
        if collection not in self.storage:
            self.storage[collection] = {}
            self.vectors[collection] = np.empty((0, self.embedding_dim))
            self.index_map[collection] = []

        # If item has no vector, we can't search it by vector, but can store it.
        # For this MVP, we assume vectors are provided or handled by the LLM layer before storage.
        if item.vector is None:
             # Just store metadata if no vector
             self.storage[collection][item.id] = item
             return True

        vector = np.array(item.vector)
        if vector.shape[0] != self.embedding_dim:
            raise ValueError(f"Vector dimension mismatch. Expected {self.embedding_dim}, got {vector.shape[0]}")

        self.storage[collection][item.id] = item

        # Simple append for now. In a real DB this is optimized.
        self.vectors[collection] = np.vstack([self.vectors[collection], vector])
        self.index_map[collection].append(item.id)
        return True

    async def retrieve(self, query: str, limit: int = 5, collection: str = "default") -> List[MemoryObject]:
        # Basic keyword search simulation or just return recent items if no vector search
        if collection not in self.storage:
            return []

        # Return most recent items for now as a fallback
        items = list(self.storage[collection].values())
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items[:limit]

    async def search_by_vector(self, vector: List[float], limit: int = 5, collection: str = "default") -> List[MemoryObject]:
        if collection not in self.vectors or len(self.vectors[collection]) == 0:
            return []

        query_vector = np.array(vector)

        # Cosine Similarity: (A . B) / (||A|| * ||B||)
        # Assuming vectors are normalized can simplify, but let's do full calc

        matrix = self.vectors[collection]
        norm_matrix = np.linalg.norm(matrix, axis=1)
        norm_query = np.linalg.norm(query_vector)

        if norm_query == 0:
            return []

        # Avoid division by zero
        norm_matrix[norm_matrix == 0] = 1e-10

        similarities = np.dot(matrix, query_vector) / (norm_matrix * norm_query)

        # Get top k indices
        # argsort returns lowest to highest, so we take the last k and reverse
        top_k_indices = np.argsort(similarities)[-limit:][::-1]

        results = []
        for idx in top_k_indices:
            mem_id = self.index_map[collection][idx]
            results.append(self.storage[collection][mem_id])

        return results

    async def clear(self, collection: str = "default"):
        if collection in self.storage:
            self.storage[collection] = {}
            self.vectors[collection] = np.empty((0, self.embedding_dim))
            self.index_map[collection] = []
