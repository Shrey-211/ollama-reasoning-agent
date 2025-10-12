import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ollama_client import OllamaClient
from src.sentiment import SentimentAnalyzer
from src.document_store import DocumentStore
from src.memory_store import MemoryStore
from src.learning_store import LearningStore
from src.agent import ReasoningAgent

if __name__ == "__main__":
    print("Starting Ollama reasoning agent (modular OOP)")
    ollama = OllamaClient(model="llama3")
    sentiment = SentimentAnalyzer()
    docs = DocumentStore(docs_dir="./docs")
    memory = MemoryStore(memory_dir="./memory")
    learning = LearningStore(learning_dir="./learnings")
    agent = ReasoningAgent(ollama, docs, sentiment, memory, learning)

    while True:
        user = input("You: ")
        if not user:
            continue
        if user.strip().lower() in ("exit", "quit"):
            break
        out = agent.handle(user)
        print("\n--- Final Reply ---\n")
        print(out["final"])
        print("\n--- Debug ---\n")
        import json
        print(json.dumps({"agent_output": out["agent_output"], "tool_out": out["tool_out"], "sentiment": out["sentiment"]}, indent=2))
        print("\n")
