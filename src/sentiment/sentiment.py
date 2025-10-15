from typing import Optional
from pydantic import BaseModel, Field
from ..functions.sentiment_functions import get_sentiment_function

class SentimentOutput(BaseModel):
    label: str
    score: float
    reasoning: str
    
    def model_dump(self):
        return {"label": self.label, "score": self.score, "reasoning": self.reasoning}


class SentimentAnalyzer:
    def __init__(self, ollama_client):
        if not ollama_client:
            raise ValueError("SentimentAnalyzer requires an ollama_client instance.")
        self.ollama = ollama_client
        print("[sentiment] using LLM-based sentiment analysis")

    def analyze(self, text: str) -> SentimentOutput:
        print(f"[sentiment] Analyzing: {text[:50]}")
        messages = [
            {"role": "system", "content": "You are a sentiment analysis expert."},
            {"role": "user", "content": f"Analyze the sentiment of this text: '{text}'"}
        ]

        result = self.ollama.chat(messages, model="gpt-4o-mini", functions=[get_sentiment_function()])
        print(f"[sentiment] Result keys: {list(result.keys())}")

        if "function_name" in result:
            args = result["arguments"]
            sentiment = SentimentOutput(label=args["label"].upper(), score=args["score"], reasoning=args["reasoning"])
            if sentiment.label not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
                raise ValueError(f"Invalid label returned: {sentiment.label}")
            return sentiment
        
        raise ValueError(f"No function call returned, got: {result}")
