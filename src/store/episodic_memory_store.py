from typing import List, Dict, Optional, Any
import json
import time
import uuid
from datetime import datetime
import chromadb
from chromadb.config import Settings


class EpisodicMemory:
    def __init__(self, what: str, when: float, where: str, who: str, emotional_context: Dict[str, Any], importance: float, memory_id: str = None):
        self.id = memory_id or str(uuid.uuid4())
        self.what = what
        self.when = when
        self.where = where
        self.who = who
        self.emotional_context = emotional_context
        self.importance = importance
        self.access_count = 0
        self.last_access = when
        self.created_at = when
        self.associations = []

    def to_dict(self):
        return {
            "id": self.id,
            "what": self.what,
            "when": self.when,
            "where": self.where,
            "who": self.who,
            "emotional_context": self.emotional_context,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_access": self.last_access,
            "created_at": self.created_at,
            "associations": self.associations
        }


class EpisodicMemoryStore:
    def __init__(self, ollama_client, persist_directory: str = "./memory"):
        self.ollama = ollama_client
        self.client = chromadb.PersistentClient(path=persist_directory, settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(name="episodic_memories", metadata={"hnsw:space": "cosine"})
        self.decay_rate = 0.95

    def _compute_importance(self, what: str, emotional_context: Dict[str, Any], recency: float) -> float:
        messages = [
            {"role": "system", "content": "You are a memory importance evaluator. Score 0-1 based on emotional intensity, novelty, and significance."},
            {"role": "user", "content": f"Event: {what}\nEmotion: {emotional_context.get('label', 'NEUTRAL')} (score: {emotional_context.get('score', 0.5)})\nRecency hours: {recency}\nRate importance 0-1:"}
        ]
        
        functions = [{
            "name": "rate_importance",
            "description": "Rate memory importance",
            "parameters": {
                "type": "object",
                "properties": {
                    "importance": {"type": "number", "minimum": 0, "maximum": 1},
                    "reasoning": {"type": "string"}
                },
                "required": ["importance", "reasoning"]
            }
        }]
        
        result = self.ollama.chat(messages, functions=functions)
        if "function_name" in result:
            return result["arguments"]["importance"]
        return 0.5

    def add_memory(self, what: str, where: str = "", who: str = "", emotional_context: Dict[str, Any] = None) -> str:
        now = time.time()
        if not emotional_context:
            emotional_context = {"label": "NEUTRAL", "score": 0.5}
        
        importance = self._compute_importance(what, emotional_context, 0)
        memory = EpisodicMemory(what, now, where, who, emotional_context, importance)
        
        metadata = {
            "when": memory.when,
            "where": memory.where,
            "who": memory.who,
            "emotion_label": emotional_context.get("label", "NEUTRAL"),
            "emotion_score": emotional_context.get("score", 0.5),
            "importance": importance,
            "access_count": 0,
            "last_access": now,
            "created_at": now
        }
        
        self.collection.add(ids=[memory.id], documents=[what], metadatas=[metadata])
        self._create_associations(memory.id, what)
        return memory.id

    def _create_associations(self, memory_id: str, content: str):
        results = self.collection.query(query_texts=[content], n_results=5, where={"$and": [{"importance": {"$gte": 0.3}}]})
        
        if results["ids"] and results["ids"][0]:
            similar_ids = [mid for mid in results["ids"][0] if mid != memory_id][:3]
            if similar_ids:
                mem = self.collection.get(ids=[memory_id])
                if mem["metadatas"]:
                    current_meta = mem["metadatas"][0]
                    current_meta["associations"] = json.dumps(similar_ids)
                    self.collection.update(ids=[memory_id], metadatas=[current_meta])

    def retrieve_memories(self, query: str, n_results: int = 5, min_importance: float = 0.0) -> List[Dict[str, Any]]:
        now = time.time()
        results = self.collection.query(query_texts=[query], n_results=n_results * 2, where={"importance": {"$gte": min_importance}})
        
        memories = []
        if results["ids"] and results["ids"][0]:
            for i, mid in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i]
                decayed_importance = self._apply_decay(meta["importance"], meta["created_at"], now)
                
                if decayed_importance >= min_importance:
                    meta["access_count"] += 1
                    meta["last_access"] = now
                    meta["importance"] = decayed_importance
                    self.collection.update(ids=[mid], metadatas=[meta])
                    
                    memories.append({
                        "id": mid,
                        "content": results["documents"][0][i],
                        "importance": decayed_importance,
                        "when": meta["when"],
                        "where": meta.get("where", ""),
                        "who": meta.get("who", ""),
                        "emotional_context": {"label": meta.get("emotion_label", "NEUTRAL"), "score": meta.get("emotion_score", 0.5)}
                    })
        
        return sorted(memories, key=lambda x: x["importance"], reverse=True)[:n_results]

    def _apply_decay(self, importance: float, created_at: float, current_time: float) -> float:
        days_elapsed = (current_time - created_at) / 86400
        return importance * (self.decay_rate ** days_elapsed)

    def consolidate_memories(self, similarity_threshold: float = 0.85):
        all_memories = self.collection.get()
        if not all_memories["ids"] or len(all_memories["ids"]) < 2:
            return
        
        for i, mid in enumerate(all_memories["ids"]):
            content = all_memories["documents"][i]
            results = self.collection.query(query_texts=[content], n_results=3)
            
            if results["ids"] and results["ids"][0] and len(results["ids"][0]) > 1:
                similar_id = results["ids"][0][1]
                if similar_id != mid:
                    self._merge_memories(mid, similar_id)

    def _merge_memories(self, id1: str, id2: str):
        mem1 = self.collection.get(ids=[id1])
        mem2 = self.collection.get(ids=[id2])
        
        if not mem1["metadatas"] or not mem2["metadatas"]:
            return
        
        meta1, meta2 = mem1["metadatas"][0], mem2["metadatas"][0]
        merged_importance = max(meta1["importance"], meta2["importance"]) * 1.1
        merged_importance = min(merged_importance, 1.0)
        
        meta1["importance"] = merged_importance
        meta1["access_count"] = meta1["access_count"] + meta2["access_count"]
        self.collection.update(ids=[id1], metadatas=[meta1])
        self.collection.delete(ids=[id2])
