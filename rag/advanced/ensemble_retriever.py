"""Ensemble retriever: combine multiple retrievers with weights"""
from typing import List, Any

class EnsembleRetriever:
    def __init__(self, retrievers: List[Any], weights: List[float] = None):
        self.retrievers = retrievers
        self.weights = weights or [1.0 / len(retrievers)] * len(retrievers)

    def retrieve(self, query: str, top_k: int = 5):
        scored = {}
        for retriever, w in zip(self.retrievers, self.weights):
            hits = retriever.retrieve(query, top_k=top_k)
            for idx, h in enumerate(hits):
                key = getattr(h, 'id', None) or str(h)
                score = (top_k - idx) * w
                if key in scored:
                    scored[key]['score'] += score
                else:
                    scored[key] = {'item': h, 'score': score}
        ordered = sorted(scored.values(), key=lambda x: x['score'], reverse=True)
        return [o['item'] for o in ordered[:top_k]]
