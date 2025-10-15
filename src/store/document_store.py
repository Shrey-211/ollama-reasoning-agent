from typing import List, Dict, Any
import os
import glob
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except Exception:
    CHROMA_AVAILABLE = False

class DocumentStore:
    def __init__(self, docs_dir: str = "./docs"):
        self.docs_dir = docs_dir
        os.makedirs(docs_dir, exist_ok=True)
        
        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(
                path=os.path.join(docs_dir, ".chroma"),
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            self._load_and_index()
            print(f"[docs] Using ChromaDB with semantic search - indexed {self.collection.count()} documents")
        else:
            self.client = None
            self.collection = None
            print('[docs] ChromaDB not available - DocumentStore disabled')

    def _load_and_index(self):
        files = glob.glob(os.path.join(self.docs_dir, "*.txt"))
        
        existing_ids = set(self.collection.get()['ids'])
        
        for f in files:
            doc_id = f"DOC-{os.path.basename(f)}"
            
            if doc_id in existing_ids:
                continue
            
            with open(f, "r", encoding="utf-8") as fh:
                content = fh.read()
            
            if content.strip():
                self.collection.add(
                    documents=[content],
                    metadatas=[{"source": os.path.basename(f), "path": f}],
                    ids=[doc_id]
                )

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        if not CHROMA_AVAILABLE or not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            documents = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    doc = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    documents.append({
                        "source": metadata.get('source', 'unknown'),
                        "text": doc[:300] + ("..." if len(doc) > 300 else ""),
                        "score": 1 - distance
                    })
            
            return documents
        except Exception as e:
            print(f"[docs] Search error: {e}")
            return []
