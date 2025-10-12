from typing import Dict, Any, List, Optional
import datetime
import random
import re

class Tools:
    @staticmethod
    def calculator(expr: str) -> Dict[str, Any]:
        """Advanced calculator with validation and detailed feedback"""
        allowed = set("0123456789+-*/(). ")
        if not set(expr) <= allowed:
            return {"error": "Expression contains unsafe characters", "suggestion": "Use only numbers and operators: + - * / ( )"}
        try:
            result = eval(expr)
            return {
                "result": result,
                "expression": expr,
                "type": type(result).__name__,
                "formatted": f"{expr} = {result}"
            }
        except ZeroDivisionError:
            return {"error": "Division by zero", "suggestion": "Cannot divide by zero"}
        except Exception as e:
            return {"error": str(e), "suggestion": "Check your mathematical expression syntax"}

    @staticmethod
    def get_datetime(timezone: str = "UTC") -> Dict[str, Any]:
        """Get current date and time with formatting"""
        now = datetime.datetime.now()
        return {
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day": now.strftime("%A"),
            "timestamp": now.timestamp(),
            "formatted": now.strftime("%B %d, %Y at %I:%M %p")
        }

    @staticmethod
    def text_analysis(text: str) -> Dict[str, Any]:
        """Analyze text for various metrics"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        return {
            "char_count": len(text),
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
            "unique_words": len(set(w.lower() for w in words)),
            "has_questions": '?' in text,
            "has_exclamations": '!' in text
        }

    @staticmethod
    def generate_id(prefix: str = "ID") -> Dict[str, Any]:
        """Generate unique identifiers"""
        timestamp = int(datetime.datetime.now().timestamp() * 1000)
        random_part = random.randint(1000, 9999)
        return {
            "id": f"{prefix}-{timestamp}-{random_part}",
            "timestamp": timestamp,
            "prefix": prefix
        }

    @staticmethod
    def string_transform(text: str, operation: str = "upper") -> Dict[str, Any]:
        """Transform strings with various operations"""
        operations = {
            "upper": text.upper(),
            "lower": text.lower(),
            "title": text.title(),
            "reverse": text[::-1],
            "capitalize": text.capitalize(),
            "snake_case": text.lower().replace(" ", "_"),
            "kebab-case": text.lower().replace(" ", "-")
        }
        result = operations.get(operation, text)
        return {
            "original": text,
            "operation": operation,
            "result": result,
            "available_operations": list(operations.keys())
        }

    @staticmethod
    def list_operations(items: List[Any], operation: str = "count") -> Dict[str, Any]:
        """Perform operations on lists"""
        try:
            if operation == "count":
                return {"count": len(items), "items": items}
            elif operation == "sum" and all(isinstance(x, (int, float)) for x in items):
                return {"sum": sum(items), "count": len(items), "average": sum(items)/len(items) if items else 0}
            elif operation == "unique":
                return {"unique": list(set(items)), "original_count": len(items), "unique_count": len(set(items))}
            elif operation == "sort":
                return {"sorted": sorted(items), "original": items}
            else:
                return {"error": f"Unknown operation: {operation}"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def validate_data(data: str, data_type: str = "email") -> Dict[str, Any]:
        """Validate various data formats"""
        patterns = {
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "url": r'^https?://[^\s]+$',
            "phone": r'^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$',
            "ip": r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        }
        pattern = patterns.get(data_type)
        if not pattern:
            return {"error": f"Unknown data type: {data_type}", "available_types": list(patterns.keys())}
        
        is_valid = bool(re.match(pattern, data))
        return {
            "valid": is_valid,
            "data": data,
            "type": data_type,
            "message": f"Valid {data_type}" if is_valid else f"Invalid {data_type} format"
        }

    @staticmethod
    def escalate(reason: str, priority: str = "medium") -> Dict[str, Any]:
        """Escalate to human with priority and context"""
        return {
            "escalated": True,
            "reason": reason,
            "priority": priority,
            "timestamp": datetime.datetime.now().isoformat(),
            "ticket_id": f"ESC-{int(datetime.datetime.now().timestamp())}",
            "message": f"Escalated to human operator: {reason}"
        }

    @staticmethod
    def format_search_results(hits: List[Dict[str, Any]]) -> str:
        """Format document search results with enhanced readability"""
        if not hits:
            return "No documents found. Try refining your search query."
        out = [f"Found {len(hits)} relevant document(s):\n"]
        for i, h in enumerate(hits, 1):
            relevance = "High" if h['score'] > 0.5 else "Medium" if h['score'] > 0.2 else "Low"
            out.append(f"{i}. [{relevance} Relevance] {h['source']} (score: {h['score']:.3f})\n{h['text']}\n")
        return "\n---\n".join(out)

    @staticmethod
    def format_memories(memories: List[Dict[str, Any]]) -> str:
        """Format memory recall results"""
        if not memories:
            return "No memories found."
        out = [f"Found {len(memories)} memory(ies):\n"]
        for i, m in enumerate(memories, 1):
            score = m.get('relevance_score', 0)
            relevance = "High" if score > 0.5 else "Medium" if score > 0.2 else "Low" if score > 0 else "Exact"
            out.append(f"{i}. [{relevance}] {m['content'][:200]}\nCategory: {m.get('category', 'general')} | Tags: {', '.join(m.get('tags', []))} | Accessed: {m.get('access_count', 0)} times\n")
        return "\n---\n".join(out)
