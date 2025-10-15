from typing import List, Dict, Any
import os
import json
import datetime

class LearningStore:
    def __init__(self, learning_dir: str = "./learnings"):
        self.learning_dir = learning_dir
        self.learning_file = os.path.join(learning_dir, "learnings.json")
        self.learnings = {}
        os.makedirs(learning_dir, exist_ok=True)
        self._load_learnings()

    def _load_learnings(self):
        if os.path.exists(self.learning_file):
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                self.learnings = json.load(f)

    def _save_learnings(self):
        with open(self.learning_file, 'w', encoding='utf-8') as f:
            json.dump(self.learnings, f, indent=2, ensure_ascii=False)

    def teach(self, name: str, steps: List[str], description: str = "", tags: List[str] = None) -> Dict[str, Any]:
        learning_id = f"LEARN-{name.lower().replace(' ', '_')}"
        
        self.learnings[learning_id] = {
            "id": learning_id,
            "name": name,
            "description": description,
            "steps": steps,
            "tags": tags or [],
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "execution_count": 0
        }
        
        self._save_learnings()
        return {
            "success": True,
            "learning_id": learning_id,
            "message": f"Learned: {name} with {len(steps)} steps"
        }

    def get_learning(self, name: str = None, learning_id: str = None) -> Dict[str, Any]:
        if learning_id and learning_id in self.learnings:
            return {"success": True, "learning": self.learnings[learning_id]}
        
        if name:
            search_id = f"LEARN-{name.lower().replace(' ', '_')}"
            if search_id in self.learnings:
                return {"success": True, "learning": self.learnings[search_id]}
            
            for lid, learning in self.learnings.items():
                if name.lower() in learning['name'].lower():
                    return {"success": True, "learning": learning}
        
        return {"success": False, "message": "Learning not found"}

    def execute_learning(self, name: str = None, learning_id: str = None) -> Dict[str, Any]:
        result = self.get_learning(name, learning_id)
        if not result['success']:
            return result
        
        learning = result['learning']
        learning['execution_count'] += 1
        learning['last_executed'] = datetime.datetime.now().isoformat()
        self._save_learnings()
        
        return {
            "success": True,
            "learning_id": learning['id'],
            "name": learning['name'],
            "steps": learning['steps'],
            "description": learning['description']
        }

    def update_learning(self, learning_id: str, name: str = None, steps: List[str] = None, 
                       description: str = None, tags: List[str] = None) -> Dict[str, Any]:
        if learning_id not in self.learnings:
            return {"success": False, "message": "Learning not found"}
        
        learning = self.learnings[learning_id]
        
        if name:
            learning['name'] = name
        if steps:
            learning['steps'] = steps
        if description is not None:
            learning['description'] = description
        if tags is not None:
            learning['tags'] = tags
        
        learning['updated_at'] = datetime.datetime.now().isoformat()
        self._save_learnings()
        
        return {
            "success": True,
            "learning_id": learning_id,
            "message": f"Updated learning: {learning['name']}"
        }

    def delete_learning(self, learning_id: str = None, name: str = None) -> Dict[str, Any]:
        if learning_id and learning_id in self.learnings:
            del self.learnings[learning_id]
            self._save_learnings()
            return {"success": True, "message": f"Deleted learning: {learning_id}"}
        
        if name:
            search_id = f"LEARN-{name.lower().replace(' ', '_')}"
            if search_id in self.learnings:
                del self.learnings[search_id]
                self._save_learnings()
                return {"success": True, "message": f"Deleted learning: {name}"}
        
        return {"success": False, "message": "Learning not found"}

    def list_learnings(self, tag: str = None) -> List[Dict[str, Any]]:
        learnings = []
        for learning in self.learnings.values():
            if tag and tag not in learning.get('tags', []):
                continue
            learnings.append(learning)
        
        return sorted(learnings, key=lambda x: x.get('execution_count', 0), reverse=True)

    def search_learnings(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        
        for learning in self.learnings.values():
            if (query_lower in learning['name'].lower() or 
                query_lower in learning.get('description', '').lower() or
                any(query_lower in step.lower() for step in learning['steps'])):
                results.append(learning)
        
        return results

    def get_stats(self) -> Dict[str, Any]:
        if not self.learnings:
            return {"total": 0, "most_used": [], "tags": {}}
        
        tags = {}
        for learning in self.learnings.values():
            for tag in learning.get('tags', []):
                tags[tag] = tags.get(tag, 0) + 1
        
        most_used = sorted(self.learnings.values(), key=lambda x: x.get('execution_count', 0), reverse=True)[:5]
        
        return {
            "total": len(self.learnings),
            "most_used": [{"name": l['name'], "executions": l.get('execution_count', 0)} for l in most_used],
            "tags": tags
        }
