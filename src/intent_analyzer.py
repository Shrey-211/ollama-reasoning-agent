from typing import Dict, Any
import json
from .ollama_client import OllamaClient

class IntentAnalyzer:
    def __init__(self, ollama: OllamaClient):
        self.ollama = ollama

    def analyze_intent(self, user_message: str) -> Dict[str, Any]:
        """Deep intent analysis using LLM reasoning"""
        
        prompt = f"""Analyze the user's intent deeply. Return ONLY valid JSON.

User message: "{user_message}"

Analyze:
1. Primary intent (what does user want?)
2. Secondary intents (any sub-goals?)
3. Entities mentioned (names, dates, numbers, etc.)
4. Action required (what should be done?)
5. Context clues (implicit information)
6. Urgency level (low/medium/high)
7. Complexity (simple/moderate/complex)

Return JSON:
{{
  "primary_intent": "string",
  "secondary_intents": ["string"],
  "entities": {{"type": "value"}},
  "action_required": "string",
  "context_clues": ["string"],
  "urgency": "low|medium|high",
  "complexity": "simple|moderate|complex",
  "suggested_tools": ["tool_name"],
  "confidence": 0.0-1.0,
  "reasoning": "why this interpretation"
}}"""

        messages = [
            {"role": "system", "content": "You are an expert intent analyzer. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.ollama.chat(messages)
        
        try:
            intent_data = json.loads(response)
        except:
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                intent_data = json.loads(response[start:end])
            except:
                intent_data = {
                    "primary_intent": "unknown",
                    "secondary_intents": [],
                    "entities": {},
                    "action_required": user_message,
                    "context_clues": [],
                    "urgency": "medium",
                    "complexity": "simple",
                    "suggested_tools": [],
                    "confidence": 0.5,
                    "reasoning": "Failed to parse LLM response"
                }
        
        return intent_data

    def map_intent_to_tool(self, intent_analysis: Dict[str, Any]) -> str:
        """Map analyzed intent to specific tool"""
        
        primary = intent_analysis.get("primary_intent", "").lower()
        suggested = intent_analysis.get("suggested_tools", [])
        
        # Direct tool mapping
        tool_keywords = {
            "search_docs": ["search", "find", "lookup", "document", "knowledge", "information"],
            "calculator": ["calculate", "compute", "math", "add", "subtract", "multiply", "divide"],
            "get_datetime": ["time", "date", "today", "now", "when", "current"],
            "text_analysis": ["analyze text", "word count", "character count", "text metrics"],
            "generate_id": ["generate id", "create id", "unique id", "identifier"],
            "string_transform": ["uppercase", "lowercase", "reverse", "transform", "convert text"],
            "validate_data": ["validate", "check email", "verify", "check url", "check phone"],
            "remember": ["remember", "store", "save", "keep in mind", "note that"],
            "recall": ["recall", "what did i", "do you remember", "retrieve memory"],
            "forget": ["forget", "delete memory", "remove memory", "erase"],
            "teach": ["teach", "learn", "procedure", "workflow", "steps", "how to"],
            "execute_learning": ["execute", "run", "follow", "do the", "perform"],
            "list_learnings": ["list learnings", "show procedures", "what workflows"],
            "escalate": ["escalate", "human help", "talk to person", "need assistance"]
        }
        
        # Check suggested tools first
        if suggested:
            return suggested[0]
        
        # Match keywords
        for tool, keywords in tool_keywords.items():
            if any(kw in primary for kw in keywords):
                return tool
        
        return "search_docs"  # Default fallback
