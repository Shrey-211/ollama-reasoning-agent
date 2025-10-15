from typing import Dict, Any, List
import threading


class ContinuousLearning:
    def __init__(self, ollama_client, learning_store):
        self.ollama = ollama_client
        self.learning = learning_store
        self.conversation_buffer = []

    def process_message(self, user_msg: str, agent_response: str):
        self.conversation_buffer.append({"user": user_msg, "agent": agent_response})
        
        if len(self.conversation_buffer) >= 3:
            threading.Thread(target=self._extract_learning, daemon=True).start()

    def _extract_learning(self):
        recent = self.conversation_buffer[-5:]
        
        messages = [
            {"role": "system", "content": "Extract teachable patterns from conversation. Identify if user is teaching you something (facts, procedures, preferences)."},
            {"role": "user", "content": str(recent)}
        ]
        
        functions = [{
            "name": "extract_teaching",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_teaching": {"type": "boolean"},
                    "learning_type": {"type": "string", "enum": ["fact", "procedure", "preference", "none"]},
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["is_teaching", "learning_type", "confidence"]
            }
        }]
        
        result = self.ollama.chat(messages, functions=functions)
        
        if "function_name" in result:
            args = result["arguments"]
            
            if args["is_teaching"] and args["confidence"] >= 0.7:
                if args["learning_type"] == "procedure" and args.get("steps"):
                    self.learning.teach(
                        name=args.get("name", "learned_procedure"),
                        steps=args["steps"],
                        description=args.get("content", ""),
                        tags=["continuous_learning", args["learning_type"]]
                    )

    def extract_explicit_teaching(self, user_msg: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "User is explicitly teaching you. Extract the learning."},
            {"role": "user", "content": user_msg}
        ]
        
        functions = [{
            "name": "parse_teaching",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["fact", "procedure", "preference"]},
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"}
                },
                "required": ["name", "type"]
            }
        }]
        
        result = self.ollama.chat(messages, functions=functions)
        
        if "function_name" in result:
            args = result["arguments"]
            
            if args["type"] == "procedure":
                return self.learning.teach(
                    name=args["name"],
                    steps=args.get("steps", [args.get("description", "")]),
                    description=args.get("description", ""),
                    tags=["explicit_teaching"]
                )
            else:
                return {"success": True, "type": args["type"], "stored_as": "episodic_memory"}
        
        return {"success": False, "message": "Could not parse teaching"}
