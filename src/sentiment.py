from typing import Optional
from pydantic import BaseModel, Field

class SentimentOutput(BaseModel):
    model_config = {"extra": "forbid", "json_schema_extra": {"additionalProperties": False}}

    label: str = Field(description="POSITIVE, NEGATIVE, or NEUTRAL")
    score: float = Field(ge=0, le=1, description="Confidence score between 0 and 1")
    reasoning: str = Field(description="Brief explanation")


class SentimentAnalyzer:
    def __init__(self, ollama_client):
        if not ollama_client:
            raise ValueError("SentimentAnalyzer requires an ollama_client instance.")
        self.ollama = ollama_client
        print("[sentiment] using LLM-based sentiment analysis")

    def analyze(self, text: str) -> SentimentOutput:
        prompt = f"""
Analyze the sentiment of this text and respond strictly in JSON format:
{{
  "label": "POSITIVE | NEGATIVE | NEUTRAL",
  "score": <float between 0 and 1>,
  "reasoning": "<brief explanation>"
}}

Text: "{text}"
"""

        messages = [
            {"role": "system", "content": "You are a sentiment analysis expert."},
            {"role": "user", "content": prompt}
        ]

        result = self.ollama.chat(
            messages,
            model="gpt-4o-mini",
            response_format=SentimentOutput
        )

        if not isinstance(result, SentimentOutput):
            result = SentimentOutput.model_validate(result)

        result.label = result.label.upper()
        if result.label not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
            raise ValueError(f"Invalid label returned: {result.label}")

        return result
