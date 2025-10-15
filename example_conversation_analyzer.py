"""
Example: Conversation analyzer extracting user interests and patterns
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.llm_client.ollama_client import OllamaClient
from src.store.conversation_analyzer import ConversationAnalyzer

def simulate_conversations():
    print("=== Conversation Analyzer Example ===\n")
    
    ollama = OllamaClient(model="gpt-4o-mini")
    analyzer = ConversationAnalyzer(ollama, persist_dir="./memory_example")
    
    # Simulate 100+ messages over time
    print("📊 Simulating 100+ conversations...\n")
    
    conversations = [
        # AWS/Cloud interest
        ("How do I deploy to AWS?", "You can use AWS CLI or console.", {"label": "NEUTRAL", "score": 0.6}),
        ("What's the best EC2 instance type?", "It depends on your workload.", {"label": "NEUTRAL", "score": 0.5}),
        ("Help me with Lambda functions", "Lambda is serverless compute.", {"label": "NEUTRAL", "score": 0.5}),
        ("I need to set up S3 buckets", "S3 is object storage.", {"label": "NEUTRAL", "score": 0.5}),
        ("CloudFormation vs Terraform?", "Both are IaC tools.", {"label": "NEUTRAL", "score": 0.6}),
        
        # Python programming
        ("How do I use decorators in Python?", "Decorators wrap functions.", {"label": "NEUTRAL", "score": 0.6}),
        ("Explain Python async/await", "It's for concurrent programming.", {"label": "NEUTRAL", "score": 0.7}),
        ("Best Python testing framework?", "pytest is popular.", {"label": "NEUTRAL", "score": 0.5}),
        ("How to optimize Python code?", "Use profiling tools.", {"label": "NEUTRAL", "score": 0.6}),
        
        # Docker/Containers
        ("Docker compose tutorial", "Here's how to use docker-compose.", {"label": "NEUTRAL", "score": 0.5}),
        ("Multi-stage Docker builds?", "They reduce image size.", {"label": "NEUTRAL", "score": 0.6}),
        ("Kubernetes vs Docker Swarm", "Kubernetes is more feature-rich.", {"label": "NEUTRAL", "score": 0.5}),
        
        # Frustration patterns
        ("This deployment keeps failing!", "Let me help troubleshoot.", {"label": "NEGATIVE", "score": 0.8}),
        ("I'm stuck on this bug", "Let's debug together.", {"label": "NEGATIVE", "score": 0.7}),
        
        # Learning goals
        ("I want to learn microservices", "Great goal! Start with basics.", {"label": "POSITIVE", "score": 0.7}),
        ("Need to master Kubernetes", "I can help with that.", {"label": "POSITIVE", "score": 0.6}),
    ]
    
    # Repeat to reach 100+ messages
    all_conversations = conversations * 7  # 112 messages
    
    for i, (user, agent, sentiment) in enumerate(all_conversations, 1):
        analyzer.log_conversation(user, agent, sentiment)
        if i % 20 == 0:
            print(f"   Logged {i} conversations...")
    
    print(f"\n✅ Logged {len(all_conversations)} conversations\n")
    
    # Trigger analysis
    print("⏳ Running background analysis (extracting patterns)...\n")
    time.sleep(3)
    
    # Get user profile
    profile = analyzer.get_user_profile()
    
    print("👤 USER PROFILE EXTRACTED:\n")
    print(f"📌 Primary Interests:")
    for interest in profile.get("primary_interests", [])[:5]:
        print(f"   - {interest}")
    
    print(f"\n💬 Frequent Topics:")
    for topic in profile.get("frequent_topics", [])[:5]:
        print(f"   - {topic}")
    
    print(f"\n🎯 Expertise Areas:")
    for area in profile.get("expertise_areas", [])[:5]:
        print(f"   - {area}")
    
    print(f"\n📚 Learning Goals:")
    for goal in profile.get("learning_goals", [])[:5]:
        print(f"   - {goal}")
    
    print(f"\n🗣️ Communication Style:")
    print(f"   {profile.get('communication_style', 'N/A')}")
    
    print(f"\n😊 Emotional Patterns:")
    print(f"   {profile.get('emotional_patterns', 'N/A')}")
    
    print(f"\n📊 Analysis Stats:")
    print(f"   Total messages analyzed: {profile.get('total_messages_analyzed', 0)}")
    print(f"   Last updated: {profile.get('last_updated', 'N/A')}")
    
    print("\n=== How Agent Uses This ===")
    print("✓ Personalizes responses based on interests")
    print("✓ Suggests relevant topics proactively")
    print("✓ Adapts communication style")
    print("✓ Recommends learning resources aligned with goals")
    print("✓ Detects emotional patterns and adjusts tone")
    
    print("\n=== Triggers ===")
    print("✓ Every 100 messages → Full analysis")
    print("✓ Every 1 hour → Time-based analysis")
    print("✓ Runs in background (non-blocking)")
    print("✓ Profile persisted to JSON file")

if __name__ == "__main__":
    simulate_conversations()
