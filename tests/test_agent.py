import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from src.llm_client.ollama_client import OllamaClient
from src.sentiment.sentiment import SentimentAnalyzer
from src.intent_analyser.intent_analyzer import IntentAnalyzer
from src.functions.sentiment_functions import get_sentiment_function
from src.functions.intent_functions import get_intent_function
from src.functions.tool_selection_functions import get_tool_selection_function

def test_ollama_client_basic():
    print("\n=== Testing OllamaClient Basic Call ===")
    ollama = OllamaClient()
    messages = [{"role": "user", "content": "Say hello"}]
    result = ollama.chat(messages)
    print(f"Result type: {type(result)}")
    print(f"Result: {result[:100] if isinstance(result, str) else result}")
    assert result is not None

def test_sentiment_function_call():
    print("\n=== Testing Sentiment Function Call ===")
    ollama = OllamaClient()
    messages = [
        {"role": "system", "content": "You are a sentiment analysis expert."},
        {"role": "user", "content": "Analyze the sentiment of this text: 'hello'"}
    ]
    result = ollama.chat(messages, model="gpt-4o-mini", functions=[get_sentiment_function()])
    print(f"Result keys: {list(result.keys())}")
    print(f"Result: {result}")
    assert "function_name" in result or "content" in result
    if "function_name" in result:
        assert "arguments" in result
        print(f"Arguments: {result['arguments']}")

def test_intent_function_call():
    print("\n=== Testing Intent Function Call ===")
    ollama = OllamaClient()
    messages = [
        {"role": "system", "content": "You are an expert intent analyzer."},
        {"role": "user", "content": "Analyze the user's intent deeply for this message: 'hello'"}
    ]
    result = ollama.chat(messages, model="gpt-4o-mini", functions=[get_intent_function()])
    print(f"Result keys: {list(result.keys())}")
    print(f"Result: {result}")
    assert "function_name" in result or "content" in result
    if "function_name" in result:
        assert "arguments" in result
        print(f"Arguments keys: {list(result['arguments'].keys())}")

def test_tool_selection_function_call():
    print("\n=== Testing Tool Selection Function Call ===")
    ollama = OllamaClient()
    messages = [
        {"role": "system", "content": "You are a helpful assistant that selects the right tool based on user intent."},
        {"role": "user", "content": "User message: hello\nIntent: greeting\nAction: respond with a greeting\nSelect the appropriate tool and provide arguments."}
    ]
    result = ollama.chat(messages, model="gpt-4o", functions=[get_tool_selection_function()])
    print(f"Result keys: {list(result.keys())}")
    print(f"Result: {result}")
    assert "function_name" in result or "content" in result
    if "function_name" in result:
        assert "arguments" in result
        args = result["arguments"]
        print(f"Arguments keys: {list(args.keys())}")
        assert "intent" in args
        assert "reasoning" in args
        has_tool_args = "tool_arguments" in args
        print(f"Has 'tool_arguments' field: {has_tool_args}")
        if has_tool_args:
            print(f"Tool arguments: {args['tool_arguments']}")

def test_sentiment_analyzer():
    print("\n=== Testing SentimentAnalyzer ===")
    ollama = OllamaClient()
    sentiment = SentimentAnalyzer(ollama_client=ollama)
    result = sentiment.analyze("hello")
    print(f"Sentiment: {result.label}, Score: {result.score}")
    assert result.label in ["POSITIVE", "NEGATIVE", "NEUTRAL"]
    assert 0 <= result.score <= 1

def test_intent_analyzer():
    print("\n=== Testing IntentAnalyzer ===")
    ollama = OllamaClient()
    intent_analyzer = IntentAnalyzer(ollama)
    result = intent_analyzer.analyze_intent("hello")
    print(f"Intent: {result}")
    assert "primary_intent" in result
    assert "action_required" in result

if __name__ == "__main__":
    print("Starting individual LLM call tests...\n")
    try:
        test_ollama_client_basic()
        test_sentiment_function_call()
        test_intent_function_call()
        test_tool_selection_function_call()
        test_sentiment_analyzer()
        test_intent_analyzer()
        print("\n[PASS] All tests passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
