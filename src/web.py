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

ollama = OllamaClient(model=os.getenv("OLLAMA_MODEL", "deepseek-r1:8b"))
sentiment = SentimentAnalyzer()
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
        'reply': result['final'],
        'logs': result.get('logs', []),
        'debug': {
            'intent': result.get('agent_output', {}).get('intent', 'unknown'),
            'sentiment': result['sentiment']['label'],
            'sentiment_score': result['sentiment']['score'],
            'tool': result.get('tool_out', {}).get('tool', 'none'),
            'reasoning': result.get('agent_output', {}).get('reasoning', ''),
            'intent_analysis': result.get('intent_analysis', {})
        }
    })

if __name__ == '__main__':
    print("\n🚀 Starting Ollama Reasoning Agent Web UI")
    print("📍 Open http://localhost:5000 in your browser\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
