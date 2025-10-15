from typing import Optional, Dict, Any
import json
from pydantic import BaseModel, Field
from ..llm_client.ollama_client import OllamaClient
from ..sentiment.sentiment import SentimentAnalyzer
from ..store.document_store import DocumentStore
from ..store.memory_store import MemoryStore
from ..store.learning_store import LearningStore
from ..intent_analyser.intent_analyzer import IntentAnalyzer
from ..tools import Tools

class AgentOutput(BaseModel):
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "properties": {
                "arguments": {
                    "type": "object",
                    "additionalProperties": False
                }
            }
        }
    }
    
    intent: str = Field(description="The tool/action to execute")
    arguments: Dict[str, Any] = Field(description="Arguments for the tool")
    reasoning: str = Field(description="Why this tool was chosen")

class ReasoningAgent:
    def __init__(self, ollama: OllamaClient, docs: DocumentStore, sentiment: SentimentAnalyzer, memory: MemoryStore = None, learning: LearningStore = None):
        self.ollama = ollama
        self.docs = docs
        self.sentiment = sentiment
        self.memory = memory or MemoryStore()
        self.learning = learning or LearningStore()
        self.intent_analyzer = IntentAnalyzer(ollama)

    def _build_structured_prompt(self, user_message: str, intent_analysis: Dict[str, Any] = None) -> str:
        
        examples = [
            {"user": "my name is John", "output": {"intent": "remember", "arguments": {"content": "my name is John", "category": "personal"}, "reasoning": "store name"}},
            {"user": "remember that I like pizza", "output": {"intent": "remember", "arguments": {"content": "I like pizza", "category": "preferences"}, "reasoning": "store preference"}},
            {"user": "what do you know about me?", "output": {"intent": "recall", "arguments": {"query": "user information", "k": 5}, "reasoning": "retrieve memories"}},
            {"user": "calculate 5+3", "output": {"intent": "calculator", "arguments": {"expr": "5+3"}, "reasoning": "math operation"}}
        ]
        
        examples_str = "\n".join([f"User: {ex['user']}\nJSON: {json.dumps(ex['output'])}" for ex in examples])
        
        prompt = f"""You are a tool selector. Return ONLY valid JSON.

Examples:
{examples_str}

Now respond to:
User: {user_message}
JSON:"""
        return prompt

    def _run_tool(self, ao: AgentOutput) -> Dict[str, Any]:
        intent = ao.intent
        args = ao.arguments if ao.arguments else {}
        
        if intent == "search_docs":
            q = args.get("query") or args.get("q") or ""
            k = int(args.get("k", 3))
            hits = self.docs.search(q, k=k)
            return {"tool": "search_docs", "result": hits}
        
        elif intent == "calculator":
            expr = args.get("expr") or args.get("expression") or ""
            return {"tool": "calculator", "result": Tools.calculator(expr)}
        
        elif intent == "get_datetime":
            tz = args.get("timezone", "UTC")
            return {"tool": "get_datetime", "result": Tools.get_datetime(tz)}
        
        elif intent == "text_analysis":
            text = args.get("text", "")
            return {"tool": "text_analysis", "result": Tools.text_analysis(text)}
        
        elif intent == "generate_id":
            prefix = args.get("prefix", "ID")
            return {"tool": "generate_id", "result": Tools.generate_id(prefix)}
        
        elif intent == "string_transform":
            text = args.get("text", "")
            operation = args.get("operation", "upper")
            return {"tool": "string_transform", "result": Tools.string_transform(text, operation)}
        
        elif intent == "list_operations":
            items = args.get("items", [])
            operation = args.get("operation", "count")
            return {"tool": "list_operations", "result": Tools.list_operations(items, operation)}
        
        elif intent == "validate_data":
            data = args.get("data", "")
            data_type = args.get("data_type", "email")
            return {"tool": "validate_data", "result": Tools.validate_data(data, data_type)}
        
        elif intent == "remember":
            content = args.get("content", "")
            tags = args.get("tags", [])
            category = args.get("category", "general")
            return {"tool": "remember", "result": self.memory.remember(content, tags, category)}
        
        elif intent == "recall":
            query = args.get("query", "")
            k = int(args.get("k", 3))
            memories = self.memory.recall(query, k)
            return {"tool": "recall", "result": memories}
        
        elif intent == "forget":
            memory_id = args.get("memory_id")
            query = args.get("query")
            return {"tool": "forget", "result": self.memory.forget(memory_id, query)}
        
        elif intent == "list_memories":
            category = args.get("category")
            limit = int(args.get("limit", 10))
            return {"tool": "list_memories", "result": self.memory.list_all(category, limit)}
        
        elif intent == "memory_stats":
            return {"tool": "memory_stats", "result": self.memory.get_stats()}
        
        elif intent == "teach":
            name = args.get("name", "")
            steps = args.get("steps", [])
            description = args.get("description", "")
            tags = args.get("tags", [])
            return {"tool": "teach", "result": self.learning.teach(name, steps, description, tags)}
        
        elif intent == "execute_learning":
            name = args.get("name")
            learning_id = args.get("learning_id")
            return {"tool": "execute_learning", "result": self.learning.execute_learning(name, learning_id)}
        
        elif intent == "get_learning":
            name = args.get("name")
            learning_id = args.get("learning_id")
            return {"tool": "get_learning", "result": self.learning.get_learning(name, learning_id)}
        
        elif intent == "update_learning":
            learning_id = args.get("learning_id", "")
            name = args.get("name")
            steps = args.get("steps")
            description = args.get("description")
            tags = args.get("tags")
            return {"tool": "update_learning", "result": self.learning.update_learning(learning_id, name, steps, description, tags)}
        
        elif intent == "delete_learning":
            learning_id = args.get("learning_id")
            name = args.get("name")
            return {"tool": "delete_learning", "result": self.learning.delete_learning(learning_id, name)}
        
        elif intent == "list_learnings":
            tag = args.get("tag")
            return {"tool": "list_learnings", "result": self.learning.list_learnings(tag)}
        
        elif intent == "search_learnings":
            query = args.get("query", "")
            return {"tool": "search_learnings", "result": self.learning.search_learnings(query)}
        
        elif intent == "learning_stats":
            return {"tool": "learning_stats", "result": self.learning.get_stats()}
        
        elif intent == "escalate":
            reason = args.get("reason", "user request")
            priority = args.get("priority", "medium")
            return {"tool": "escalate", "result": Tools.escalate(reason, priority)}
        
        return {"tool": "none", "result": None}

    def _synthesize_final(self, user_message: str, ao: AgentOutput, tool_out: Dict[str, Any]) -> str:
        system = "You are an assistant. Use the tool_output to craft a concise user-facing reply."
        payload = {"user_message": user_message, "agent_decision": ao.model_dump(), "tool_output": tool_out}
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(payload, indent=2)}
        ]
        # Use gpt-4o for final synthesis (best quality response)
        resp = self.ollama.chat(messages, model="gpt-4o")
        return resp

    def handle(self, user_message: str) -> Dict[str, Any]:
        logs = []
        logs.append(f"[INPUT] User message: {user_message}")
        
        # Step 1: Deep Intent Analysis
        logs.append("[INTENT_ANALYSIS] Starting deep intent analysis...")
        intent_analysis = self.intent_analyzer.analyze_intent(user_message)
        logs.append(f"[INTENT_ANALYSIS] Primary: {intent_analysis.get('primary_intent')}")
        logs.append(f"[INTENT_ANALYSIS] Action: {intent_analysis.get('action_required')}")
        logs.append(f"[INTENT_ANALYSIS] Urgency: {intent_analysis.get('urgency')}, Complexity: {intent_analysis.get('complexity')}")
        logs.append(f"[INTENT_ANALYSIS] Confidence: {intent_analysis.get('confidence', 0):.2f}")
        logs.append(f"[INTENT_ANALYSIS] Reasoning: {intent_analysis.get('reasoning', 'N/A')}")
        
        # Step 2: Sentiment Analysis (LLM-based)
        sent = self.sentiment.analyze(user_message)
        logs.append(f"[SENTIMENT] Label: {sent.label}, Score: {sent.score:.3f}")
        if sent.reasoning:
            logs.append(f"[SENTIMENT] Reasoning: {sent.reasoning}")
        
        if sent.label == "NEGATIVE" and sent.score >= 0.8:
            logs.append("[DECISION] Escalating due to strong negative sentiment")
            return {"final": "Escalating to human operator due to strong negative sentiment.", "meta": {"sentiment": sent.model_dump(), "intent_analysis": intent_analysis}, "logs": logs}
        
        # Step 3: Build flexible prompt with intent context
        prompt = self._build_structured_prompt(user_message, intent_analysis)
        logs.append(f"[PROMPT] Built flexible prompt with examples")
        
        messages = [{"role": "system", "content": "You are a helpful assistant that selects the right tool based on user intent."}, {"role": "user", "content": prompt}]
        # Use gpt-4o for tool selection with structured output
        ao = self.ollama.chat(messages, model="gpt-4o", response_format=AgentOutput)
        logs.append(f"[TOOL_SELECTION] Intent: {ao.intent}, Args: {ao.arguments}")
        logs.append(f"[REASONING] {ao.reasoning}")
        
        tool_out = self._run_tool(ao)
        logs.append(f"[TOOL] Executed {tool_out.get('tool')}, Result: {str(tool_out.get('result'))[:100]}...")
        
        final = self._synthesize_final(user_message, ao, tool_out)
        logs.append(f"[SYNTHESIS] Generated final response")
        logs.append(f"[FINAL_ANSWER] {final}")
        
        return {"final": final, "agent_output": ao.model_dump(), "tool_out": tool_out, "sentiment": sent.model_dump(), "intent_analysis": intent_analysis, "logs": logs}
