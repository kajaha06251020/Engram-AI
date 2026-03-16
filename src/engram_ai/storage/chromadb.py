import logging
import chromadb
from engram_ai.models.experience import Experience
from engram_ai.models.skill import Skill
from engram_ai.storage.base import BaseStorage

logger = logging.getLogger(__name__)

class ChromaDBStorage(BaseStorage):
    """ChromaDB-backed vector storage for experiences and skills."""

    def __init__(self, persist_path: str) -> None:
        self._client = chromadb.PersistentClient(path=persist_path)
        self._experiences = self._client.get_or_create_collection(
            name="experiences", metadata={"hnsw:space": "cosine"})
        self._skills = self._client.get_or_create_collection(
            name="skills", metadata={"hnsw:space": "cosine"})

    def store_experience(self, experience: Experience) -> str:
        doc = f"{experience.action} | {experience.context} | {experience.outcome}"
        self._experiences.add(
            ids=[experience.id], documents=[doc],
            metadatas=[{"data": experience.model_dump_json(), "valence": experience.valence, "status": experience.status}])
        return experience.id

    def query_experiences(self, context: str, k: int = 5) -> list[tuple[Experience, float]]:
        count = self._experiences.count()
        if count == 0:
            return []
        results = self._experiences.query(query_texts=[context], n_results=min(k, count))
        output = []
        for i, meta in enumerate(results["metadatas"][0]):
            exp = Experience.model_validate_json(meta["data"])
            distance = results["distances"][0][i]
            similarity = max(0.0, 1.0 - distance)
            output.append((exp, similarity))
        return output

    def get_all_experiences(self) -> list[Experience]:
        results = self._experiences.get()
        return [Experience.model_validate_json(meta["data"]) for meta in results["metadatas"]]

    def store_skill(self, skill: Skill) -> str:
        doc = f"{skill.rule} | {skill.context_pattern}"
        self._skills.add(
            ids=[skill.id], documents=[doc],
            metadatas=[{"data": skill.model_dump_json(), "confidence": skill.confidence, "applied": "false"}])
        return skill.id

    def get_all_skills(self) -> list[Skill]:
        results = self._skills.get()
        return [Skill.model_validate_json(meta["data"]) for meta in results["metadatas"]]

    def get_unapplied_skills(self) -> list[Skill]:
        results = self._skills.get(where={"applied": "false"})
        return [Skill.model_validate_json(meta["data"]) for meta in results["metadatas"]]

    def mark_skills_applied(self, skill_ids: list[str]) -> None:
        for skill_id in skill_ids:
            existing = self._skills.get(ids=[skill_id])
            if existing["metadatas"]:
                meta = existing["metadatas"][0]
                meta["applied"] = "true"
                self._skills.update(ids=[skill_id], metadatas=[meta])
