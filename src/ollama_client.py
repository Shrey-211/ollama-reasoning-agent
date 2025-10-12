from typing import List, Dict
import json
import os
try:
    import ollama
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False

class OllamaClient:
    def __init__(self, model: str = "deepseek-r1:8b"):
        self.model = model
        if OLLAMA_AVAILABLE and os.getenv('OLLAMA_HOST'):
            ollama.Client(host=os.getenv('OLLAMA_HOST'))
        if not OLLAMA_AVAILABLE:
            print("[ollama] not available — using mock client")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        if OLLAMA_AVAILABLE:
            client = ollama.Client(host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
            resp = client.chat(model=self.model, messages=messages)
            return resp.get("message", {}).get("content", "")
        # Mock behavior: return JSON intent based on heuristics
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") in ("user", "assistant"):
                user_msg = m.get("content", "")
                break
        lower = user_msg.lower()
        if any(w in lower for w in ("price", "pricing", "cost", "docs")):
            out = {"intent": "search_docs", "arguments": {"query": user_msg, "k": 3}, "sentiment": "neutral", "reasoning": "docs"}
        elif any(w in lower for w in ("calculate", "compute", "+", "-", "*", "/")):
            out = {"intent": "calculator", "arguments": {"expr": "13 * 12"}, "sentiment": "neutral", "reasoning": "calc"}
        else:
            out = {"intent": "search_docs", "arguments": {"query": user_msg, "k": 2}, "sentiment": "neutral", "reasoning": "default"}
        return json.dumps(out)
