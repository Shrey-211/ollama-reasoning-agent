import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify
from src.ollama_client import OllamaClient
from src.sentiment import SentimentAnalyzer
from src.document_store import DocumentStore
from src.memory_store import MemoryStore
from src.learning_store import LearningStore
from src.agent import ReasoningAgent

app = Flask(__name__)

ollama = OllamaClient(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
sentiment = SentimentAnalyzer(ollama_client=ollama)
docs = DocumentStore(docs_dir="./docs")
memory = MemoryStore(memory_dir="./memory")
learning = LearningStore(learning_dir="./learnings")
agent = ReasoningAgent(ollama, docs, sentiment, memory, learning)

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    result = agent.handle(user_message)
    
    # Print logs to console
    print("\n" + "="*60)
    for log in result.get('logs', []):
        print(log)
    print("="*60 + "\n")
    
    return jsonify({
        'reply': result.get('final', 'No response'),
        'logs': result.get('logs', []),
        'debug': {
            'intent': result.get('agent_output', {}).get('intent', 'escalate'),
            'sentiment': result.get('sentiment', result.get('meta', {}).get('sentiment', {})).get('label', 'unknown'),
            'sentiment_score': result.get('sentiment', result.get('meta', {}).get('sentiment', {})).get('score', 0),
            'tool': result.get('tool_out', {}).get('tool', 'escalate'),
            'reasoning': result.get('agent_output', {}).get('reasoning', 'escalated'),
            'intent_analysis': result.get('intent_analysis', {})
        }
    })

if __name__ == '__main__':
    print("\n🚀 Starting Ollama Reasoning Agent Web UI")
    print("📍 Open http://localhost:5000 in your browser\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
