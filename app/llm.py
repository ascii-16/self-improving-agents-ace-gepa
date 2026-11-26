
import ollama

EXECUTION_MODEL = "qwen3.5:4b"
OPTIMIZER_MODEL = "qwen3.5:9b-q4_K_M"

class OllamaClient:

    def __init__(self, model: str = EXECUTION_MODEL):
        self.model = model
        self.client = ollama.Client(host="http://localhost:11434")

    def chat(self, messages: list, tools: list | None = None):
        return self.client.chat(
            model=self.model,
            messages=messages,
            tools=tools or [],
            options={
                "temperature": 0.2,
                "num_ctx": 8192,
            },
        )
