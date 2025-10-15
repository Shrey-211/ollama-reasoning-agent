def get_tool_selection_function():
    return {
        "name": "select_tool",
        "description": "Select the appropriate tool to execute based on user intent and provide tool_arguments",
        "parameters": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "The tool/action to execute",
                    "enum": [
                        "search_docs", "calculator", "get_datetime", "text_analysis",
                        "generate_id", "string_transform", "list_operations", "validate_data",
                        "remember", "recall", "forget", "list_memories", "memory_stats",
                        "teach", "execute_learning", "get_learning", "update_learning",
                        "delete_learning", "list_learnings", "search_learnings", "learning_stats",
                        "user_profile", "escalate"
                    ]
                },
                "tool_arguments": {
                    "type": "object",
                    "description": "Arguments for the selected tool as key-value pairs",
                    "additionalProperties": True
                },
                "reasoning": {
                    "type": "string",
                    "description": "Why this tool was chosen"
                }
            },
            "required": ["intent", "tool_arguments", "reasoning"]
        }
    }
