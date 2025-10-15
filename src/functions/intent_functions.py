def get_intent_function():
    return {
        "name": "analyze_intent",
        "description": "Deep analysis of user intent including primary intent, action required, urgency, complexity, and confidence",
        "parameters": {
            "type": "object",
            "properties": {
                "primary_intent": {
                    "type": "string",
                    "description": "Main intent of the user"
                },
                "action_required": {
                    "type": "string",
                    "description": "What action should be taken"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Urgency level"
                },
                "complexity": {
                    "type": "string",
                    "enum": ["simple", "moderate", "complex"],
                    "description": "Complexity level"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence score between 0 and 1"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation of the analysis"
                }
            },
            "required": ["primary_intent", "action_required", "urgency", "complexity", "confidence", "reasoning"]
        }
    }
