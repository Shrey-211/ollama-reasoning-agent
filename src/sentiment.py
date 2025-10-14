from typing import Dict
from pydantic import BaseModel, Field

class SentimentOutput(BaseModel):
    label: str = Field(description="POSITIVE, NEGATIVE, or NEUTRAL")
    score: float = Field(description="Confidence score 0-1")
    reasoning: str = Field(description="Brief explanation")

class SentimentAnalyzer:
    def __init__(self, ollama_client=None):
        self.ollama = ollama_client
        if not ollama_client:
            raise Exception("SentimentAnalyzer requires ollama_client")
        print("[sentiment] using LLM-based sentiment analysis")

    def analyze(self, text: str) -> Dict[str, float]:
        prompt = f"""Analyze the sentiment of this text.

Text: "{text}"

Determine if the sentiment is POSITIVE, NEGATIVE, or NEUTRAL with a confidence score."""

        messages = [
            {"role": "system", "content": "You are a sentiment analysis expert."},
            {"role": "user", "content": prompt}
        ]
        
        # Use structured output
        result = self.ollama.chat(messages, model="gpt-4o-mini", response_format=SentimentOutput)
        return {
            "label": result.label.upper(),
            "score": result.score,
            "reasoning": result.reasoning
        }
