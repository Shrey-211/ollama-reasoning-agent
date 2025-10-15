def get_sentiment_function():
    return {
        "name": "analyze_sentiment",
        "description": "Analyze sentiment of text and return label (POSITIVE/NEGATIVE/NEUTRAL), confidence score, and reasoning",
        "parameters": {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "enum": ["POSITIVE", "NEGATIVE", "NEUTRAL"],
                    "description": "Sentiment classification"
                },
                "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence score between 0 and 1"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of the sentiment analysis"
                }
            },
            "required": ["label", "score", "reasoning"]
        }
    }
