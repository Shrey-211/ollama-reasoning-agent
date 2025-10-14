from typing import List, Dict, Optional, Type
import json
import os
from pydantic import BaseModel
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

class OllamaClient:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        if OPENAI_AVAILABLE:
            self.client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY'),
                base_url=os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
            )
            print(f"[openai] Using OpenAI with model: {model}")
        else:
            self.client = None
            raise Exception("OpenAI not available - install openai package")

    def chat(self, messages: List[Dict[str, str]], model: str = None, response_format: Optional[Type[BaseModel]] = None) -> str:
        use_model = model or self.model
        if not OPENAI_AVAILABLE or not self.client:
            raise Exception("OpenAI client not initialized")
        
        try:
            if response_format:
                # Use structured output with Pydantic model
                response = self.client.beta.chat.completions.parse(
                    model=use_model,
                    messages=messages,
                    response_format=response_format
                )
                return response.choices[0].message.parsed
            else:
                # Regular text response
                response = self.client.chat.completions.create(
                    model=use_model,
                    messages=messages
                )
                return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

