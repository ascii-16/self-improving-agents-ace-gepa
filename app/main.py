
from app.agent import Agent


def main():
    agent = Agent()

    print("\nSelf-Improving Agent — Baseline")
    print("Model: Qwen 3.5 4B")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("exit", "quit"):
            break

        if not user_input:
            continue

        try:
            response = agent.run(user_input)
            print(f"\nAgent: {response}\n")
        except Exception as exc:
            print(f"\nError: {exc}\n")


if __name__ == "__main__":
    main()
