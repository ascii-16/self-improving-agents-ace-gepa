
import json
import time

from pathlib import Path

from app.agent import Agent
from app.evaluation.evaluator import evaluate_task
from app.evaluation.metrics import calculate_metrics


BENCHMARK_PATH = Path("data/benchmarks.json")
TRACE_PATH = Path("traces/executions.jsonl")
RESULT_PATH = Path("artifacts/baseline_results.json")


def get_new_trace_events(offset: int) -> list[dict]:
    if not TRACE_PATH.exists():
        return []

    with TRACE_PATH.open() as file:
        file.seek(offset)
        lines = file.readlines()

    return [
        json.loads(line)
        for line in lines
        if line.strip()
    ]


def run_benchmarks():

    tasks = json.loads(BENCHMARK_PATH.read_text())

    results = []

    for index, task in enumerate(tasks, start=1):

        print(
            f"\n[{index}/{len(tasks)}] "
            f"Running {task['id']}"
        )

        offset = (
            TRACE_PATH.stat().st_size
            if TRACE_PATH.exists()
            else 0
        )

        start = time.perf_counter()

        agent = Agent()

        try:
            output = agent.run(task["input"])
        except Exception as exc:
            output = ""
            print(f"Execution error: {exc}")

        duration = time.perf_counter() - start

        events = get_new_trace_events(offset)

        actual_tools = [
            event["tool"]
            for event in events
            if event.get("event") == "tool_called"
        ]

        result = evaluate_task(
            task=task,
            output=output,
            actual_tools=actual_tools,
        )

        result["duration_seconds"] = round(duration, 2)

        results.append(result)

        print(
            f"Score: {result['overall_score']:.2f} | "
            f"Success: {result['success']} | "
            f"Tools: {actual_tools}"
        )

    metrics = calculate_metrics(results)

    report = {
        "experiment": "baseline",
        "model": "qwen3.5:4b",
        "metrics": metrics,
        "results": results,
    }

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    RESULT_PATH.write_text(
        json.dumps(report, indent=2)
    )

    print("\n========== BASELINE RESULTS ==========")
    print(json.dumps(metrics, indent=2))

    return report


if __name__ == "__main__":
    run_benchmarks()
