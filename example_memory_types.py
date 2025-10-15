"""
Example demonstrating different memory types working together.
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.llm_client.ollama_client import OllamaClient
from src.store.episodic_memory_store import EpisodicMemoryStore
from src.store.learning_store import LearningStore
from src.store.memory_types import MemoryTypes

def example_memory_types():
    print("=== Memory Types Example ===\n")
    
    ollama = OllamaClient(model="gpt-4o-mini")
    episodic = EpisodicMemoryStore(ollama, persist_directory="./memory_example")
    learning = LearningStore(learning_dir="./learnings")
    memory_types = MemoryTypes(ollama, episodic, learning, persist_dir="./memory_example")
    
    # Simulate conversation
    print("💬 Conversation Flow:\n")
    
    interactions = [
        ("What's 2+2?", "2+2 equals 4.", {"label": "NEUTRAL", "score": 0.5}),
        ("How do I deploy to AWS?", "You can use AWS CLI or console.", {"label": "NEUTRAL", "score": 0.6}),
        ("I'm frustrated with deployment", "I understand. Let me help.", {"label": "NEGATIVE", "score": 0.7}),
        ("Remember: my AWS account is prod-123", "I'll remember that.", {"label": "NEUTRAL", "score": 0.5}),
        ("What was my AWS account again?", "Your AWS account is prod-123.", {"label": "NEUTRAL", "score": 0.5}),
    ]
    
    for i, (user, agent, sentiment) in enumerate(interactions, 1):
        print(f"{i}. User: {user}")
        print(f"   Agent: {agent}")
        
        explicit = "remember" in user.lower()
        memory_types.add_interaction(user, agent, sentiment, explicit_remember=explicit)
        
        if explicit:
            print("   ⚡ Explicit remember - High priority for long-term storage")
        print()
    
    # Wait for background processing
    print("⏳ Background processing (short-term summary + long-term extraction)...\n")
    time.sleep(2)
    
    # Show short-term memory
    print("📝 SHORT-TERM MEMORY (Working Memory - Last 5 interactions):")
    short_term = memory_types.get_short_term_context()
    print(f"   Summary: {short_term}\n")
    
    # Show long-term memory
    print("🧠 LONG-TERM MEMORY (Consolidated Important Events):")
    long_term = episodic.retrieve_memories("AWS account", n_results=3, min_importance=0.0)
    for mem in long_term:
        print(f"   - {mem['content'][:80]}... (importance: {mem['importance']:.2f})")
    print()
    
    # Show procedural memory
    print("🔧 PROCEDURAL MEMORY (Skills & How-To):")
    learning.teach(
        name="deploy_to_aws",
        steps=["Configure AWS CLI", "Run deployment script", "Verify deployment"],
        description="Standard AWS deployment procedure",
        tags=["aws", "deployment"]
    )
    procedures = memory_types.get_procedural_memory("deploy")
    for proc in procedures:
        print(f"   - {proc['name']}: {len(proc['steps'])} steps")
    print()
    
    print("=== Memory Types Summary ===")
    print("✓ SHORT-TERM: JSON file updated every 5 messages (background)")
    print("✓ LONG-TERM: LLM extracts important facts → Episodic store")
    print("✓ SEMANTIC: Document store (existing)")
    print("✓ PROCEDURAL: Learning store (existing)")
    print("✓ Explicit 'remember' → High priority storage")
    print("✓ All processing happens in background threads")

if __name__ == "__main__":
    example_memory_types()
