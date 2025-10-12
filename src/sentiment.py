from typing import Dict
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False

class SentimentAnalyzer:
    def __init__(self):
        if TRANSFORMERS_AVAILABLE:
            try:
                self.pipe = pipeline("sentiment-analysis")
                print("[sentiment] using transformers pipeline")
            except Exception:
                self.pipe = None
        else:
            self.pipe = None
            print("[sentiment] transformers not available - fallback")

    def analyze(self, text: str) -> Dict[str, float]:
        if self.pipe:
            r = self.pipe(text, truncation=True)[0]
            return {"label": r.get("label").upper(), "score": float(r.get("score", 0.0))}
        txt = text.lower()
        neg_words = ["not", "can't", "failed", "frustrat", "angry", "sad", "upset"]
        pos_words = ["happy", "great", "awesome", "finished", "thanks"]
        neg = sum(1 for w in neg_words if w in txt)
        pos = sum(1 for w in pos_words if w in txt)
        if neg > pos:
            return {"label": "NEGATIVE", "score": min(0.99, 0.5 + 0.1*(neg-pos))}
        if pos > neg:
            return {"label": "POSITIVE", "score": min(0.99, 0.5 + 0.1*(pos-neg))}
        return {"label": "NEUTRAL", "score": 0.5}
