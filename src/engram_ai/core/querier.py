from engram_ai.models.experience import Experience
from engram_ai.storage.base import BaseStorage

class QueryResult:
    """Result of an experience query, partitioned into best and avoid."""
    def __init__(self, best: list[tuple[Experience, float]], avoid: list[tuple[Experience, float]]):
        self.best = best
        self.avoid = avoid

    def __getitem__(self, key: str) -> list[tuple[Experience, float]]:
        if key == "best":
            return self.best
        if key == "avoid":
            return self.avoid
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        return key in ("best", "avoid")

class Querier:
    """Searches past experiences and partitions into best/avoid."""
    def __init__(self, storage: BaseStorage) -> None:
        self._storage = storage

    def query(self, context: str, k: int = 5) -> QueryResult:
        results = self._storage.query_experiences(context, k=k)
        best = []
        avoid = []
        for exp, similarity in results:
            if exp.valence > 0:
                score = similarity * exp.valence
                best.append((exp, score))
            elif exp.valence < 0:
                score = similarity * abs(exp.valence)
                avoid.append((exp, score))
        best.sort(key=lambda x: x[1], reverse=True)
        avoid.sort(key=lambda x: x[1], reverse=True)
        return QueryResult(best=best, avoid=avoid)
