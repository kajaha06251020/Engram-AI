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
        self._migrate_v1_skills()

    def _migrate_v1_skills(self) -> None:
        """Idempotent migration: add 'status' to v0.1 skills that lack it.
        Note: ChromaDB lacks $exists where filters, so we use an O(N) scan.
        This is acceptable for typical collection sizes and only updates unmigrated records.
        """
        all_records = self._skills.get()
        for i, meta in enumerate(all_records["metadatas"]):
            if "status" not in meta:
                meta["status"] = "active"
                self._skills.update(
                    ids=[all_records["ids"][i]],
                    metadatas=[meta],
                )

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
            metadatas=[{
                "data": skill.model_dump_json(),
                "confidence": skill.confidence,
                "applied": "false",
                "status": skill.status,
            }])
        return skill.id

    def get_all_skills(self) -> list[Skill]:
        results = self._skills.get(where={"status": "active"})
        return [Skill.model_validate_json(meta["data"]) for meta in results["metadatas"]]

    def get_unapplied_skills(self) -> list[Skill]:
        results = self._skills.get(where={"$and": [{"applied": "false"}, {"status": "active"}]})
        return [Skill.model_validate_json(meta["data"]) for meta in results["metadatas"]]

    def mark_skills_applied(self, skill_ids: list[str]) -> None:
        for skill_id in skill_ids:
            existing = self._skills.get(ids=[skill_id])
            if existing["metadatas"]:
                meta = existing["metadatas"][0]
                meta["applied"] = "true"
                self._skills.update(ids=[skill_id], metadatas=[meta])

    def query_skills(self, text: str, k: int = 5) -> list[tuple[Skill, float]]:
        count = self._skills.count()
        if count == 0:
            return []
        results = self._skills.query(
            query_texts=[text], n_results=min(k, count),
            where={"status": "active"},
        )
        output = []
        for i, meta in enumerate(results["metadatas"][0]):
            skill = Skill.model_validate_json(meta["data"])
            distance = results["distances"][0][i]
            similarity = max(0.0, 1.0 - distance)
            output.append((skill, similarity))
        return output

    def update_skill(self, skill: Skill) -> None:
        doc = f"{skill.rule} | {skill.context_pattern}"
        existing = self._skills.get(ids=[skill.id])
        applied = existing["metadatas"][0].get("applied", "false") if existing["metadatas"] else "false"
        self._skills.update(
            ids=[skill.id],
            documents=[doc],
            metadatas=[{
                "data": skill.model_dump_json(),
                "confidence": skill.confidence,
                "applied": applied,
                "status": skill.status,
            }],
        )

    def get_experience(self, experience_id: str) -> Experience | None:
        results = self._experiences.get(ids=[experience_id])
        if not results["metadatas"]:
            return None
        return Experience.model_validate_json(results["metadatas"][0]["data"])
