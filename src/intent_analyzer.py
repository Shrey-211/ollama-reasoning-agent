from typing import Dict, Any, List
import json
from pydantic import BaseModel, Field
from .ollama_client import OllamaClient

class IntentAnalysisOutput(BaseModel):
    model_config = {"extra": "forbid", "json_schema_extra": {"additionalProperties": False}}
    
    primary_intent: str = Field(description="Main intent of the user")
    action_required: str = Field(description="What action should be taken")
    urgency: str = Field(description="low, medium, or high")
    complexity: str = Field(description="simple, moderate, or complex")
    confidence: float = Field(description="Confidence score 0-1")
    reasoning: str = Field(description="Explanation of the analysis")

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
        
        # Use gpt-4o-mini for fast intent analysis
        # Use structured output
        result = self.ollama.chat(messages, model="gpt-4o-mini", response_format=IntentAnalysisOutput)
        return result.model_dump()

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
