from typing import Optional, Dict, Any
import json
from pydantic import BaseModel
from .ollama_client import OllamaClient
from .sentiment import SentimentAnalyzer
from .document_store import DocumentStore
from .memory_store import MemoryStore
from .learning_store import LearningStore
from .intent_analyzer import IntentAnalyzer
from .tools import Tools

class AgentOutput(BaseModel):
    intent: str
    arguments: Optional[Dict[str, Any]] = {}
    sentiment: Optional[str] = None
    reasoning: Optional[str] = None

class ReasoningAgent:
    def __init__(self, ollama: OllamaClient, docs: DocumentStore, sentiment: SentimentAnalyzer, memory: MemoryStore = None, learning: LearningStore = None):
        self.ollama = ollama
        self.docs = docs
        self.sentiment = sentiment
        self.memory = memory or MemoryStore()
        self.learning = learning or LearningStore()
        self.intent_analyzer = IntentAnalyzer(ollama)

    def _build_structured_prompt(self, user_message: str) -> str:
        schema = {"intent": "string (search_docs | calculator | get_datetime | text_analysis | generate_id | string_transform | list_operations | validate_data | remember | recall | forget | list_memories | memory_stats | teach | execute_learning | get_learning | update_learning | delete_learning | list_learnings | search_learnings | learning_stats | escalate | none)", "arguments": "object", "sentiment": "positive|neutral|negative", "reasoning": "string"}
        prompt = (
            "You must return VALID JSON exactly matching the schema. No additional text.\n"
            f"{json.dumps(schema, indent=2)}\n"
            "Available intents:\n"
            "- search_docs: Search knowledge base (args: query, k)\n"
            "- calculator: Math calculations (args: expr)\n"
            "- get_datetime: Get current date/time (args: timezone)\n"
            "- text_analysis: Analyze text metrics (args: text)\n"
            "- generate_id: Generate unique ID (args: prefix)\n"
            "- string_transform: Transform strings (args: text, operation)\n"
            "- list_operations: List operations (args: items, operation)\n"
            "- validate_data: Validate email/url/phone/ip (args: data, data_type)\n"
            "- remember: Store information in memory (args: content, tags, category)\n"
            "- recall: Retrieve memories (args: query, k)\n"
            "- forget: Delete memories (args: memory_id OR query)\n"
            "- list_memories: List all memories (args: category, limit)\n"
            "- memory_stats: Get memory statistics (args: none)\n"
            "- teach: Teach a procedure/workflow (args: name, steps, description, tags)\n"
            "- execute_learning: Execute learned procedure (args: name OR learning_id)\n"
            "- get_learning: Get learning details (args: name OR learning_id)\n"
            "- update_learning: Update learning (args: learning_id, name, steps, description, tags)\n"
            "- delete_learning: Delete learning (args: learning_id OR name)\n"
            "- list_learnings: List all learnings (args: tag)\n"
            "- search_learnings: Search learnings (args: query)\n"
            "- learning_stats: Get learning statistics (args: none)\n"
            "- escalate: Escalate to human (args: reason, priority)\n"
            "User message:\n"
            f"{user_message}\n"
        )
        return prompt

    def _parse_llm_output(self, text: str) -> Optional[AgentOutput]:
        try:
            data = json.loads(text)
        except Exception:
            try:
                s = text[text.find('{'): text.rfind('}')+1]
                data = json.loads(s)
            except Exception:
                return None
        try:
            ao = AgentOutput(**data)
            return ao
        except Exception:
            return None

    def _run_tool(self, ao: AgentOutput) -> Dict[str, Any]:
        intent = ao.intent
        args = ao.arguments or {}
        
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
        payload = {"user_message": user_message, "agent_decision": ao.dict(), "tool_output": tool_out}
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(payload, indent=2)}
        ]
        resp = self.ollama.chat(messages)
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
        
        # Step 2: Sentiment Analysis
        sent = self.sentiment.analyze(user_message)
        logs.append(f"[SENTIMENT] Label: {sent.get('label')}, Score: {sent.get('score'):.3f}")
        
        if sent.get("label") == "NEGATIVE" and sent.get("score", 0) >= 0.8:
            logs.append("[DECISION] Escalating due to strong negative sentiment")
            return {"final": "Escalating to human operator due to strong negative sentiment.", "meta": {"sentiment": sent, "intent_analysis": intent_analysis}, "logs": logs}
        
        # Step 3: Build context-aware prompt with intent analysis
        prompt = self._build_structured_prompt(user_message)
        prompt += f"\n\nIntent Analysis Context:\n{json.dumps(intent_analysis, indent=2)}\n"
        logs.append(f"[PROMPT] Built context-aware prompt with intent analysis")
        
        messages = [{"role": "system", "content": "You are a JSON-output agent."}, {"role": "user", "content": prompt}]
        llm_out = self.ollama.chat(messages)
        logs.append(f"[LLM_RAW] {llm_out[:200]}..." if len(llm_out) > 200 else f"[LLM_RAW] {llm_out}")
        
        ao = self._parse_llm_output(llm_out)
        if not ao:
            logs.append("[PARSE] Failed to parse LLM output, using fallback")
            ao = AgentOutput(intent="search_docs", arguments={"query": user_message, "k": 2}, sentiment=sent.get("label"), reasoning="fallback")
        else:
            logs.append(f"[PARSE] Intent: {ao.intent}, Args: {ao.arguments}, Reasoning: {ao.reasoning}")
        
        tool_out = self._run_tool(ao)
        logs.append(f"[TOOL] Executed {tool_out.get('tool')}, Result: {str(tool_out.get('result'))[:100]}...")
        
        final = self._synthesize_final(user_message, ao, tool_out)
        logs.append(f"[SYNTHESIS] Generated final response")
        
        return {"final": final, "agent_output": ao.dict(), "tool_out": tool_out, "sentiment": sent, "intent_analysis": intent_analysis, "logs": logs}
