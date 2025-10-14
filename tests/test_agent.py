import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ollama_client import OllamaClient
from src.sentiment import SentimentAnalyzer
from src.document_store import DocumentStore
from src.memory_store import MemoryStore
from src.agent import ReasoningAgent

def test_calculation_intent():
    ollama = OllamaClient()
    sentiment = SentimentAnalyzer(ollama_client=ollama)
    docs = DocumentStore(docs_dir="./docs")
    memory = MemoryStore(memory_dir="./test_memory")
    agent = ReasoningAgent(ollama, docs, sentiment, memory)
    out = agent.handle("Please calculate 13 * 12")
    assert out["agent_output"]["intent"] in ("calculator", "search_docs")

def test_search_intent():
    ollama = OllamaClient()
    sentiment = SentimentAnalyzer(ollama_client=ollama)
    docs = DocumentStore(docs_dir="./docs")
    memory = MemoryStore(memory_dir="./test_memory")
    agent = ReasoningAgent(ollama, docs, sentiment, memory)
    out = agent.handle("What is the pricing for your product?")
    assert out["agent_output"]["intent"] in ("search_docs",)

def test_memory_operations():
    ollama = OllamaClient()
    sentiment = SentimentAnalyzer(ollama_client=ollama)
    docs = DocumentStore(docs_dir="./docs")
    memory = MemoryStore(memory_dir="./test_memory")
    agent = ReasoningAgent(ollama, docs, sentiment, memory)
    
    out = agent.handle("Remember that my favorite color is blue")
    assert out["agent_output"]["intent"] in ("remember",)
    
    out = agent.handle("What is my favorite color?")
    assert out["agent_output"]["intent"] in ("recall", "search_docs")
