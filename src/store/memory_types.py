from typing import List, Dict, Any
import json
import os
import threading
from datetime import datetime


class MemoryTypes:
    def __init__(self, ollama_client, episodic_store, learning_store, persist_dir: str = "./memory"):
        self.ollama = ollama_client
        self.episodic = episodic_store
        self.learning = learning_store
        self.persist_dir = persist_dir
        self.short_term_path = os.path.join(persist_dir, "short_term.json")
        self.conversation_buffer = []
        self.short_term_summary = ""
        os.makedirs(persist_dir, exist_ok=True)
        self._load_short_term()

    def _load_short_term(self):
        if os.path.exists(self.short_term_path):
            with open(self.short_term_path, 'r') as f:
                data = json.load(f)
                self.conversation_buffer = data.get("buffer", [])
                self.short_term_summary = data.get("summary", "")

    def _save_short_term(self):
        with open(self.short_term_path, 'w') as f:
            json.dump({"buffer": self.conversation_buffer[-10:], "summary": self.short_term_summary}, f)

    def add_interaction(self, user_msg: str, agent_msg: str, sentiment: Dict[str, Any], explicit_remember: bool = False):
        self.conversation_buffer.append({"user": user_msg, "agent": agent_msg, "timestamp": datetime.now().isoformat(), "sentiment": sentiment})
        
        if len(self.conversation_buffer) >= 5:
            threading.Thread(target=self._process_short_term, daemon=True).start()
            threading.Thread(target=self._process_long_term, args=(explicit_remember,), daemon=True).start()

    def _process_short_term(self):
        recent = self.conversation_buffer[-5:]
        messages = [
            {"role": "system", "content": "Summarize the last 5 interactions in 2-3 sentences. Focus on key topics and user needs."},
            {"role": "user", "content": json.dumps([{"user": m["user"], "agent": m["agent"]} for m in recent])}
        ]
        
        functions = [{
            "name": "summarize_conversation",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "key_topics": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["summary", "key_topics"]
            }
        }]
        
        result = self.ollama.chat(messages, functions=functions)
        if "function_name" in result:
            self.short_term_summary = result["arguments"]["summary"]
            self._save_short_term()

    def _process_long_term(self, explicit_remember: bool):
        recent = self.conversation_buffer[-5:]
        messages = [
            {"role": "system", "content": "Extract important information worth remembering long-term. Rate importance 0-1."},
            {"role": "user", "content": json.dumps([{"user": m["user"], "agent": m["agent"], "sentiment": m["sentiment"]} for m in recent])}
        ]
        
        functions = [{
            "name": "extract_important",
            "parameters": {
                "type": "object",
                "properties": {
                    "important_facts": {"type": "array", "items": {"type": "string"}},
                    "importance_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "reasoning": {"type": "string"}
                },
                "required": ["important_facts", "importance_score"]
            }
        }]
        
        result = self.ollama.chat(messages, functions=functions)
        if "function_name" in result:
            args = result["arguments"]
            threshold = 0.5 if not explicit_remember else 0.0
            
            if args["importance_score"] >= threshold or explicit_remember:
                for fact in args["important_facts"]:
                    avg_sentiment = {"label": "NEUTRAL", "score": 0.5}
                    if recent:
                        scores = [m["sentiment"].get("score", 0.5) for m in recent]
                        avg_sentiment["score"] = sum(scores) / len(scores)
                    self.episodic.add_memory(fact, emotional_context=avg_sentiment)

    def get_short_term_context(self) -> str:
        return self.short_term_summary

    def get_procedural_memory(self, query: str) -> List[Dict[str, Any]]:
        return self.learning.search_learnings(query)
