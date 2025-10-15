from typing import Dict, Any, List
import json
import os
import time
import threading
from datetime import datetime


class ConversationAnalyzer:
    def __init__(self, ollama_client, persist_dir: str = "./memory"):
        self.ollama = ollama_client
        self.persist_dir = persist_dir
        self.conversation_log_path = os.path.join(persist_dir, "conversation_log.json")
        self.profile_path = os.path.join(persist_dir, "user_profile.json")
        self.conversations = []
        self.user_profile = {}
        self.message_count = 0
        self.last_analysis_time = time.time()
        self.analysis_interval = 3600  # 1 hour
        self.message_threshold = 100
        os.makedirs(persist_dir, exist_ok=True)
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.conversation_log_path):
            with open(self.conversation_log_path, 'r') as f:
                data = json.load(f)
                self.conversations = data.get("conversations", [])
                self.message_count = data.get("message_count", 0)
        
        if os.path.exists(self.profile_path):
            with open(self.profile_path, 'r') as f:
                self.user_profile = json.load(f)

    def _save_conversations(self):
        with open(self.conversation_log_path, 'w') as f:
            json.dump({
                "conversations": self.conversations[-500:],
                "message_count": self.message_count
            }, f)

    def _save_profile(self):
        with open(self.profile_path, 'w') as f:
            json.dump(self.user_profile, f, indent=2)

    def log_conversation(self, user_msg: str, agent_msg: str, sentiment: Dict[str, Any]):
        self.conversations.append({
            "user": user_msg,
            "agent": agent_msg,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat()
        })
        self.message_count += 1
        self._save_conversations()
        
        current_time = time.time()
        time_elapsed = current_time - self.last_analysis_time
        
        if self.message_count >= self.message_threshold or time_elapsed >= self.analysis_interval:
            threading.Thread(target=self._run_analysis, daemon=True).start()
            self.last_analysis_time = current_time
            self.message_count = 0

    def _run_analysis(self):
        recent = self.conversations[-100:] if len(self.conversations) > 100 else self.conversations
        
        messages = [
            {"role": "system", "content": "Analyze conversation history to extract user interests, topics, preferences, and behavioral patterns."},
            {"role": "user", "content": json.dumps([{"user": c["user"], "sentiment": c["sentiment"]} for c in recent])}
        ]
        
        functions = [{
            "name": "analyze_user_profile",
            "parameters": {
                "type": "object",
                "properties": {
                    "primary_interests": {"type": "array", "items": {"type": "string"}},
                    "frequent_topics": {"type": "array", "items": {"type": "string"}},
                    "communication_style": {"type": "string"},
                    "expertise_areas": {"type": "array", "items": {"type": "string"}},
                    "learning_goals": {"type": "array", "items": {"type": "string"}},
                    "preferences": {"type": "object"},
                    "emotional_patterns": {"type": "string"}
                },
                "required": ["primary_interests", "frequent_topics"]
            }
        }]
        
        result = self.ollama.chat(messages, functions=functions)
        
        if "function_name" in result:
            args = result["arguments"]
            self.user_profile = {
                "primary_interests": args.get("primary_interests", []),
                "frequent_topics": args.get("frequent_topics", []),
                "communication_style": args.get("communication_style", ""),
                "expertise_areas": args.get("expertise_areas", []),
                "learning_goals": args.get("learning_goals", []),
                "preferences": args.get("preferences", {}),
                "emotional_patterns": args.get("emotional_patterns", ""),
                "last_updated": datetime.now().isoformat(),
                "total_messages_analyzed": len(recent)
            }
            self._save_profile()

    def get_user_profile(self) -> Dict[str, Any]:
        return self.user_profile

    def get_profile_context(self) -> str:
        if not self.user_profile:
            return ""
        
        context = []
        if self.user_profile.get("primary_interests"):
            context.append(f"User interests: {', '.join(self.user_profile['primary_interests'][:3])}")
        if self.user_profile.get("expertise_areas"):
            context.append(f"Expertise: {', '.join(self.user_profile['expertise_areas'][:3])}")
        if self.user_profile.get("communication_style"):
            context.append(f"Style: {self.user_profile['communication_style']}")
        
        return " | ".join(context)
