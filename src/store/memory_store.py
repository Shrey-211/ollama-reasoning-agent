from typing import List, Dict, Any
import os
import datetime
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except Exception:
    CHROMA_AVAILABLE = False

class MemoryStore:
    def __init__(self, memory_dir: str = "./memory"):
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)
        
        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(
                path=memory_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name="memories",
                metadata={"hnsw:space": "cosine"}
            )
            print("[memory] Using ChromaDB with semantic search")
        else:
            self.client = None
            self.collection = None
            print("[memory] ChromaDB not available - memory disabled")

    def remember(self, content: str, tags: List[str] = None, category: str = "general") -> Dict[str, Any]:
        if not CHROMA_AVAILABLE:
            return {"success": False, "message": "ChromaDB not available"}
        
        memory_id = f"MEM-{int(datetime.datetime.now().timestamp() * 1000)}"
        metadata = {
            "category": category,
            "tags": ",".join(tags or []),
            "timestamp": datetime.datetime.now().isoformat(),
            "access_count": 0
        }
        
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": f"Remembered: {content[:50]}..."
        }

    def recall(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        if not CHROMA_AVAILABLE:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            memories = []
            if results['ids'] and results['ids'][0]:
                for i, mem_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i]
                    memories.append({
                        "id": mem_id,
                        "content": results['documents'][0][i],
                        "category": metadata.get('category', 'general'),
                        "tags": metadata.get('tags', '').split(',') if metadata.get('tags') else [],
                        "timestamp": metadata.get('timestamp'),
                        "access_count": metadata.get('access_count', 0),
                        "relevance_score": 1 - results['distances'][0][i] if results['distances'] else 1.0
                    })
                    
                    # Update access count
                    metadata['access_count'] = metadata.get('access_count', 0) + 1
                    self.collection.update(
                        ids=[mem_id],
                        metadatas=[metadata]
                    )
            
            return memories
        except Exception as e:
            print(f"[memory] Recall error: {e}")
            return []

    def forget(self, memory_id: str = None, query: str = None) -> Dict[str, Any]:
        if not CHROMA_AVAILABLE:
            return {"success": False, "message": "ChromaDB not available"}
        
        try:
            if memory_id:
                self.collection.delete(ids=[memory_id])
                return {"success": True, "removed": 1, "message": f"Forgot memory {memory_id}"}
            
            elif query:
                results = self.collection.query(query_texts=[query], n_results=100)
                if results['ids'] and results['ids'][0]:
                    ids_to_delete = []
                    for i, doc in enumerate(results['documents'][0]):
                        if query.lower() in doc.lower():
                            ids_to_delete.append(results['ids'][0][i])
                    
                    if ids_to_delete:
                        self.collection.delete(ids=ids_to_delete)
                        return {"success": True, "removed": len(ids_to_delete), "message": f"Forgot {len(ids_to_delete)} memories"}
                
                return {"success": False, "removed": 0, "message": "No matching memories found"}
            
            return {"success": False, "message": "Provide memory_id or query to forget"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def list_all(self, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        if not CHROMA_AVAILABLE:
            return []
        
        try:
            all_data = self.collection.get()
            memories = []
            
            for i, mem_id in enumerate(all_data['ids']):
                metadata = all_data['metadatas'][i]
                if category and metadata.get('category') != category:
                    continue
                
                memories.append({
                    "id": mem_id,
                    "content": all_data['documents'][i],
                    "category": metadata.get('category', 'general'),
                    "tags": metadata.get('tags', '').split(',') if metadata.get('tags') else [],
                    "timestamp": metadata.get('timestamp'),
                    "access_count": metadata.get('access_count', 0)
                })
            
            memories.sort(key=lambda x: x['timestamp'], reverse=True)
            return memories[:limit]
        except Exception as e:
            print(f"[memory] List error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        if not CHROMA_AVAILABLE:
            return {"total": 0, "categories": {}, "tags": {}}
        
        try:
            all_data = self.collection.get()
            total = len(all_data['ids'])
            
            categories = {}
            tags = {}
            all_memories = []
            
            for i, mem_id in enumerate(all_data['ids']):
                metadata = all_data['metadatas'][i]
                cat = metadata.get('category', 'general')
                categories[cat] = categories.get(cat, 0) + 1
                
                tag_list = metadata.get('tags', '').split(',') if metadata.get('tags') else []
                for tag in tag_list:
                    if tag:
                        tags[tag] = tags.get(tag, 0) + 1
                
                all_memories.append({
                    "id": mem_id,
                    "content": all_data['documents'][i][:50] + "...",
                    "access_count": metadata.get('access_count', 0)
                })
            
            most_accessed = sorted(all_memories, key=lambda x: x['access_count'], reverse=True)[:3]
            
            return {
                "total": total,
                "categories": categories,
                "tags": tags,
                "most_accessed": most_accessed
            }
        except Exception as e:
            print(f"[memory] Stats error: {e}")
            return {"total": 0, "categories": {}, "tags": {}}
