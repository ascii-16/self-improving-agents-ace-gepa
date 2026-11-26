
import ast
import operator
import json
from pathlib import Path


DATA_PATH = Path("data/knowledge.json")

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def calculate(expression: str):
    """Safely evaluate basic arithmetic expressions."""

    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](
                evaluate(node.left),
                evaluate(node.right),
            )

        if isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.USub, ast.UAdd)
        ):
            value = evaluate(node.operand)
            return -value if isinstance(node.op, ast.USub) else value

        raise ValueError("Unsupported expression")

    try:
        if len(expression) > 100:
            raise ValueError("Expression too long")

        result = evaluate(ast.parse(expression, mode="eval").body)

        if isinstance(result, (int, float)) and abs(result) > 1e15:
            raise ValueError("Result exceeds allowed limit")

        return {"result": result}

    except Exception as exc:
        return {"error": str(exc)}


def search_knowledge(query: str):
    """Search local knowledge documents."""

    documents = json.loads(DATA_PATH.read_text())

    query_words = set(query.lower().split())
    results = []

    for document in documents:
        content = document["content"].lower()
        title = document["title"].lower()

        score = sum(
            1 for word in query_words
            if word in content or word in title
        )

        if score:
            results.append({
                "title": document["title"],
                "content": document["content"],
                "score": score,
            })

    results.sort(key=lambda x: x["score"], reverse=True)

    return {"results": results[:5]}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate a mathematical expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Arithmetic expression"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Search the local knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


TOOL_REGISTRY = {
    "calculate": calculate,
    "search_knowledge": search_knowledge,
}
