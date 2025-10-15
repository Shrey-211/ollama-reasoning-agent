from typing import List, Dict, Optional, Any
import json
import os
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

    def chat(self, messages: List[Dict[str, str]], model: str = None, functions: Optional[List[Dict[str, Any]]] = None) -> Any:
        use_model = model or self.model
        try:
            if functions:
                print(f"[openai] Calling {use_model} with function: {functions[0]['name']}")
                response = self.client.chat.completions.create(
                    model=use_model,
                    messages=messages,
                    functions=functions,
                    function_call={"name": functions[0]["name"]} if len(functions) == 1 else "auto"
                )
                message = response.choices[0].message
                print(f"[openai] Has function_call: {hasattr(message, 'function_call') and message.function_call is not None}")
                if message.function_call:
                    args = json.loads(message.function_call.arguments)
                    print(f"[openai] Function: {message.function_call.name}, Args: {list(args.keys())}")
                    return {"function_name": message.function_call.name, "arguments": args}
                print(f"[openai] No function call, content: {message.content[:100]}")
                return {"content": message.content}
            else:
                response = self.client.chat.completions.create(model=use_model, messages=messages)
                return response.choices[0].message.content
        except Exception as e:
            print(f"[openai] ERROR: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")

