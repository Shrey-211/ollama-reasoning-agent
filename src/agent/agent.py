from typing import Optional, Dict, Any
import json
from ..llm_client.ollama_client import OllamaClient
from ..sentiment.sentiment import SentimentAnalyzer
from ..store.document_store import DocumentStore
from ..store.memory_store import MemoryStore
from ..store.learning_store import LearningStore
from ..store.episodic_memory_store import EpisodicMemoryStore
from ..store.memory_types import MemoryTypes
from ..store.continuous_learning import ContinuousLearning
from ..store.conversation_analyzer import ConversationAnalyzer
from ..intent_analyser.intent_analyzer import IntentAnalyzer
from ..functions.tool_selection_functions import get_tool_selection_function
from ..tools import Tools

class AgentOutput:
    def __init__(self, intent: str, arguments: Dict[str, Any], reasoning: str):
        self.intent = intent
        self.arguments = arguments
        self.reasoning = reasoning
    
    def model_dump(self):
        return {"intent": self.intent, "arguments": self.arguments, "reasoning": self.reasoning}

class ReasoningAgent:
    def __init__(self, ollama: OllamaClient, docs: DocumentStore, sentiment: SentimentAnalyzer, memory: MemoryStore = None, learning: LearningStore = None, episodic: EpisodicMemoryStore = None):
        self.ollama = ollama
        self.docs = docs
        self.sentiment = sentiment
        self.memory = memory or MemoryStore()
        self.learning = learning or LearningStore()
        self.episodic = episodic or EpisodicMemoryStore(ollama)
        self.memory_types = MemoryTypes(ollama, self.episodic, self.learning)
        self.continuous_learning = ContinuousLearning(ollama, self.learning)
        self.conversation_analyzer = ConversationAnalyzer(ollama)
        self.intent_analyzer = IntentAnalyzer(ollama)

    def _build_tool_selection_prompt(self, user_message: str, intent_analysis: Dict[str, Any] = None) -> str:
        context = f"User message: {user_message}\n"
        if intent_analysis:
            context += f"Intent: {intent_analysis.get('primary_intent')}\n"
            context += f"Action: {intent_analysis.get('action_required')}\n"
        return context + "Select the appropriate tool and provide arguments."

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
        
        elif intent == "user_profile":
            return {"tool": "user_profile", "result": self.conversation_analyzer.get_user_profile()}
        
        elif intent == "teach":
            name = args.get("name", "")
            steps = args.get("steps", [])
            description = args.get("description", "")
            tags = args.get("tags", [])
            
            if not steps:
                result = self.continuous_learning.extract_explicit_teaching(args.get("content", ""))
            else:
                result = self.learning.teach(name, steps, description, tags)
            
            return {"tool": "teach", "result": result}
        
        elif intent == "execute_learning":
            name = args.get("name")
            learning_id = args.get("learning_id")
            result = self.learning.execute_learning(name, learning_id)
            if result.get("success"):
                self.memory_types.add_interaction(
                    f"Execute learning: {name}",
                    f"Executed steps: {result.get('steps_executed', 0)}",
                    {"label": "NEUTRAL", "score": 0.5},
                    explicit_remember=True
                )
            return {"tool": "execute_learning", "result": result}
        
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

    def _synthesize_final(self, user_message: str, ao: AgentOutput, tool_out: Dict[str, Any], memory_context: str = "") -> str:
        system = "You are an assistant. Use the tool_output to craft a concise user-facing reply."
        if memory_context:
            system += f"\n\nRelevant past context:\n{memory_context}"
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
        
        # Get short-term working memory context
        short_term_context = self.memory_types.get_short_term_context()
        if short_term_context:
            logs.append(f"[SHORT_TERM] {short_term_context[:100]}")
        
        # Get user profile context
        profile_context = self.conversation_analyzer.get_profile_context()
        if profile_context:
            logs.append(f"[PROFILE] {profile_context}")
        
        # Retrieve relevant episodic memories (long-term)
        past_memories = self.episodic.retrieve_memories(user_message, n_results=3, min_importance=0.3)
        if past_memories:
            logs.append(f"[LONG_TERM] Retrieved {len(past_memories)} relevant memories")
        
        try:
            # Step 1: Deep Intent Analysis
            logs.append("[INTENT_ANALYSIS] Starting deep intent analysis...")
            intent_analysis = self.intent_analyzer.analyze_intent(user_message)
            logs.append(f"[INTENT_ANALYSIS] Primary: {intent_analysis.get('primary_intent')}")
            logs.append(f"[INTENT_ANALYSIS] Action: {intent_analysis.get('action_required')}")
            logs.append(f"[INTENT_ANALYSIS] Urgency: {intent_analysis.get('urgency')}, Complexity: {intent_analysis.get('complexity')}")
            logs.append(f"[INTENT_ANALYSIS] Confidence: {intent_analysis.get('confidence', 0):.2f}")
            logs.append(f"[INTENT_ANALYSIS] Reasoning: {intent_analysis.get('reasoning', 'N/A')}")
        except Exception as e:
            logs.append(f"[INTENT_ANALYSIS] Error: {str(e)}")
            intent_analysis = {"primary_intent": "unknown", "action_required": "escalate", "urgency": "medium", "complexity": "simple", "confidence": 0, "reasoning": "Analysis failed"}
        
        try:
            # Step 2: Sentiment Analysis (LLM-based)
            sent = self.sentiment.analyze(user_message)
            logs.append(f"[SENTIMENT] Label: {sent.label}, Score: {sent.score:.3f}")
            if sent.reasoning:
                logs.append(f"[SENTIMENT] Reasoning: {sent.reasoning}")
        except Exception as e:
            logs.append(f"[SENTIMENT] Error: {str(e)}")
            from ..sentiment.sentiment import SentimentOutput
            sent = SentimentOutput(label="NEUTRAL", score=0.5, reasoning="Analysis failed")
        
        if sent.label == "NEGATIVE" and sent.score >= 0.8:
            logs.append("[DECISION] Escalating due to strong negative sentiment")
            return {"final": "Escalating to human operator due to strong negative sentiment.", "meta": {"sentiment": sent.model_dump(), "intent_analysis": intent_analysis}, "logs": logs}
        
        # Step 3: Tool selection using function calling
        try:
            prompt = self._build_tool_selection_prompt(user_message, intent_analysis)
            logs.append(f"[PROMPT] Built tool selection prompt")
            print(f"[agent] Prompt: {prompt[:100]}")
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that selects the right tool based on user intent."},
                {"role": "user", "content": prompt}
            ]
            
            result = self.ollama.chat(messages, model="gpt-4o", functions=[get_tool_selection_function()])
            print(f"[agent] Result keys: {list(result.keys())}")
            
            if "function_name" not in result:
                print(f"[agent] No function_name, result: {result}")
                if "content" in result:
                    ao = AgentOutput(intent="escalate", arguments={"reason": "No structured response", "priority": "low"}, reasoning="Model returned text instead of function call")
                else:
                    raise ValueError("No function call returned for tool selection")
            else:
                args = result["arguments"]
                print(f"[agent] Args keys: {list(args.keys())}")
                ao = AgentOutput(
                    intent=args.get("intent", "escalate"),
                    arguments=args.get("tool_arguments", args.get("arguments", {})),
                    reasoning=args.get("reasoning", "No reasoning provided")
                )
            logs.append(f"[TOOL_SELECTION] Intent: {ao.intent}, Args: {ao.arguments}")
            logs.append(f"[REASONING] {ao.reasoning}")
        except Exception as e:
            print(f"[agent] Exception: {type(e).__name__}: {str(e)}")
            logs.append(f"[TOOL_SELECTION] Error: {str(e)}")
            ao = AgentOutput(intent="escalate", arguments={"reason": "Tool selection failed", "priority": "medium"}, reasoning="Error in tool selection")
        
        try:
            tool_out = self._run_tool(ao)
            logs.append(f"[TOOL] Executed {tool_out.get('tool')}, Result: {str(tool_out.get('result'))[:100]}...")
        except Exception as e:
            logs.append(f"[TOOL] Error: {str(e)}")
            tool_out = {"tool": "error", "result": {"error": str(e)}}
        
        try:
            memory_context = ""
            if profile_context:
                memory_context += f"User profile: {profile_context}\n"
            if short_term_context:
                memory_context += f"Recent conversation: {short_term_context}\n"
            if past_memories:
                memory_context += "\n".join([f"- {m['content'][:100]}" for m in past_memories[:2]])
            
            final = self._synthesize_final(user_message, ao, tool_out, memory_context)
            logs.append(f"[SYNTHESIS] Generated final response")
            logs.append(f"[FINAL_ANSWER] {final}")
        except Exception as e:
            logs.append(f"[SYNTHESIS] Error: {str(e)}")
            final = "I encountered an error processing your request. Please try again."
        
        # Add to memory types (background processing)
        try:
            explicit_remember = ao.intent == "remember"
            self.memory_types.add_interaction(user_message, final, sent.model_dump(), explicit_remember)
            logs.append("[MEMORY] Background processing initiated")
        except Exception as e:
            logs.append(f"[MEMORY] Error: {str(e)}")
        
        # Continuous learning (background)
        try:
            self.continuous_learning.process_message(user_message, final)
            logs.append("[LEARNING] Continuous learning active")
        except Exception as e:
            logs.append(f"[LEARNING] Error: {str(e)}")
        
        # Conversation analysis (background)
        try:
            self.conversation_analyzer.log_conversation(user_message, final, sent.model_dump())
            logs.append("[ANALYZER] Conversation logged")
        except Exception as e:
            logs.append(f"[ANALYZER] Error: {str(e)}")
        
        return {"final": final, "agent_output": ao.model_dump(), "tool_out": tool_out, "sentiment": sent.model_dump(), "intent_analysis": intent_analysis, "logs": logs}
