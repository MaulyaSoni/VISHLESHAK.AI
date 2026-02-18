"""Multi-query retriever: issues multiple queries and merges results"""
from typing import List, Any

class MultiQueryRetriever:
    def __init__(self, retriever, num_queries: int = 3):
        self.retriever = retriever
        self.num_queries = num_queries

    def retrieve(self, query: str, top_k: int = 5) -> List[Any]:
        results = []
        for i in range(self.num_queries):
            q = f"{query} (variation {i+1})"
            rr = self.retriever.retrieve(q, top_k=top_k)
            results.extend(rr)
        # naive dedup by id or text
        seen = set()
        merged = []
        for r in results:
            key = getattr(r, 'id', None) or str(r)
            if key not in seen:
                seen.add(key)
                merged.append(r)
        return merged[:top_k]
