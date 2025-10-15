from typing import Dict, Any
from ..llm_client.ollama_client import OllamaClient
from ..functions.intent_functions import get_intent_function

class IntentAnalyzer:
    def __init__(self, ollama: OllamaClient):
        self.ollama = ollama

    def analyze_intent(self, user_message: str) -> Dict[str, Any]:
        """Deep intent analysis using LLM reasoning"""
        print(f"[intent] Analyzing: {user_message[:50]}")
        messages = [
            {"role": "system", "content": "You are an expert intent analyzer."},
            {"role": "user", "content": f"Analyze the user's intent deeply for this message: '{user_message}'"}
        ]
        
        result = self.ollama.chat(messages, model="gpt-4o-mini", functions=[get_intent_function()])
        print(f"[intent] Result keys: {list(result.keys())}")
        
        if "function_name" in result:
            return result["arguments"]
        
        raise ValueError(f"No function call returned, got: {result}")

    def map_intent_to_tool(self, intent_analysis: Dict[str, Any]) -> str:
        """Map analyzed intent to specific tool"""
        
        primary = intent_analysis.get("primary_intent", "").lower()
        action = intent_analysis.get("action_required", "").lower()
        suggested = intent_analysis.get("suggested_tools", [])
        
        # Direct tool mapping
        tool_keywords = {
            "search_docs": ["search", "find", "lookup", "document", "knowledge", "information", "what do you know"],
            "calculator": ["calculate", "compute", "math", "add", "subtract", "multiply", "divide"],
            "get_datetime": ["time", "date", "today", "now", "when", "current"],
            "text_analysis": ["analyze text", "word count", "character count", "text metrics"],
            "generate_id": ["generate id", "create id", "unique id", "identifier"],
            "string_transform": ["uppercase", "lowercase", "reverse", "transform", "convert text"],
            "validate_data": ["validate", "check email", "verify", "check url", "check phone"],
            "remember": ["remember", "store", "save", "keep in mind", "note that", "my name is", "introduce"],
            "recall": ["recall", "what did i", "do you remember", "retrieve memory", "what do you know about me"],
            "forget": ["forget", "delete memory", "remove memory", "erase"],
            "teach": ["teach", "learn", "procedure", "workflow", "steps", "how to"],
            "execute_learning": ["execute", "run", "follow", "do the", "perform"],
            "list_learnings": ["list learnings", "show procedures", "what workflows"],
            "escalate": ["escalate", "human help", "talk to person", "need assistance"]
        }
        
        # Check suggested tools first
        if suggested:
            return suggested[0]
        
        # Match keywords in both primary intent and action
        combined = f"{primary} {action}"
        for tool, keywords in tool_keywords.items():
            if any(kw in combined for kw in keywords):
                return tool
        
        return "search_docs"  # Default fallback
