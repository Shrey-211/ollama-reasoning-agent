"""
Example: Continuous learning from natural conversation
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.llm_client.ollama_client import OllamaClient
from src.store.learning_store import LearningStore
from src.store.continuous_learning import ContinuousLearning

def example_continuous_learning():
    print("=== Continuous Learning Example ===\n")
    
    ollama = OllamaClient(model="gpt-4o-mini")
    learning = LearningStore(learning_dir="./learnings")
    continuous = ContinuousLearning(ollama, learning)
    
    print("💬 Natural Conversation:\n")
    
    # Scenario 1: User teaches implicitly through conversation
    print("--- Implicit Teaching ---")
    conversations = [
        ("How do I deploy my app?", "You can use various methods."),
        ("First I build the Docker image", "That's a good start."),
        ("Then I push it to ECR", "ECR is AWS's container registry."),
        ("Finally I update the ECS service", "That completes the deployment."),
    ]
    
    for user, agent in conversations:
        print(f"User: {user}")
        print(f"Agent: {agent}\n")
        continuous.process_message(user, agent)
    
    print("⏳ Background learning extraction...\n")
    time.sleep(2)
    
    # Check if learned
    learned = learning.search_learnings("deploy")
    if learned:
        print("✅ Agent learned procedure from conversation:")
        for l in learned:
            if "continuous_learning" in l.get("tags", []):
                print(f"   Name: {l['name']}")
                print(f"   Steps: {l['steps']}")
                print()
    
    # Scenario 2: Explicit teaching
    print("--- Explicit Teaching ---")
    print("User: 'Let me teach you how to debug Python errors'")
    print("      'Step 1: Read the error message'")
    print("      'Step 2: Check the stack trace'")
    print("      'Step 3: Add print statements'\n")
    
    result = continuous.extract_explicit_teaching(
        "Let me teach you how to debug Python errors. "
        "Step 1: Read the error message. "
        "Step 2: Check the stack trace. "
        "Step 3: Add print statements."
    )
    
    if result.get("success"):
        print(f"✅ Learned: {result.get('learning_id', 'new procedure')}\n")
    
    # Scenario 3: User corrects agent
    print("--- Learning from Corrections ---")
    print("User: 'No, that's wrong. The correct way is to use git rebase, not merge'")
    print("Agent: 'Thank you for the correction. I'll remember that.'\n")
    
    continuous.process_message(
        "No, that's wrong. The correct way is to use git rebase, not merge",
        "Thank you for the correction. I'll remember that."
    )
    
    print("⏳ Processing correction...\n")
    time.sleep(2)
    
    print("=== How It Works ===")
    print("✓ Every 3+ messages → LLM extracts teachable patterns (background)")
    print("✓ Detects: facts, procedures, preferences, corrections")
    print("✓ Confidence ≥ 0.7 → Automatically stored in learning system")
    print("✓ Explicit 'teach me' → Immediate extraction and storage")
    print("✓ Agent applies learned procedures in future conversations")
    print("\n💡 The agent learns continuously without explicit commands!")

if __name__ == "__main__":
    example_continuous_learning()
