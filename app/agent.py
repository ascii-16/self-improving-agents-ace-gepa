
from app.llm import OllamaClient
from app.tools import TOOL_SCHEMAS, TOOL_REGISTRY
from app.trace import record
from app.prompts import SYSTEM_PROMPT

class Agent:
    def __init__(self):
        self.llm = OllamaClient()
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def run(self, user_input: str):

        self.messages.append({
            "role": "user",
            "content": user_input
        })

        record({
            "event": "task_started",
            "input": user_input,
            "model": self.llm.model,
        })

        max_iterations = 8

        for iteration in range(max_iterations):

            response = self.llm.chat(
                messages=self.messages,
                tools=TOOL_SCHEMAS,
            )

            message = response.message
            self.messages.append(message)

            if not message.tool_calls:
                output = message.content or ""

                record({
                    "event": "task_completed",
                    "input": user_input,
                    "output": output,
                    "iterations": iteration + 1,
                })

                return output

            for tool_call in message.tool_calls:

                name = tool_call.function.name
                arguments = tool_call.function.arguments

                record({
                    "event": "tool_called",
                    "tool": name,
                    "arguments": arguments,
                    "iteration": iteration,
                })

                if name not in TOOL_REGISTRY:
                    result = {"error": "Unknown tool"}
                else:
                    try:
                        result = TOOL_REGISTRY[name](**arguments)
                    except Exception as exc:
                        result = {"error": str(exc)}

                record({
                    "event": "tool_completed",
                    "tool": name,
                    "result": result,
                })

                self.messages.append({
                    "role": "tool",
                    "name": name,
                    "content": str(result),
                })

        record({
            "event": "task_failed",
            "input": user_input,
            "reason": "Maximum iterations exceeded",
        })

        return "I couldn't complete the task within the execution limit."
