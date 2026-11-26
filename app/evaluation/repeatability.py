
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from app.evaluation.runner import (
    BENCHMARK_PATH,
    run_benchmarks,
)


OUTPUT_DIR = Path("artifacts/baseline_v0")
NUM_RUNS = 3

FILES_TO_HASH = [
    Path("app/prompts.py"),
    Path("app/agent.py"),
    Path("app/tools.py"),
    Path("app/llm.py"),
    Path("app/evaluation/evaluator.py"),
    Path("app/evaluation/metrics.py"),
    Path("data/benchmarks.json"),
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_experiment_fingerprints() -> dict:
    return {
        str(path): sha256_file(path)
        for path in FILES_TO_HASH
        if path.exists()
    }


def calculate_repeatability(run_reports: list[dict]) -> dict:
    metrics = [
        report["metrics"]
        for report in run_reports
    ]

    metric_names = [
        "success_rate",
        "tool_accuracy",
        "average_score",
    ]

    summary = {}

    for name in metric_names:
        values = [item[name] for item in metrics]

        summary[name] = {
            "mean": round(mean(values), 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "values": values,
        }

    # Compare each task across all runs.
    task_results = {}

    for report in run_reports:
        for result in report["results"]:
            task_id = result["task_id"]

            task_results.setdefault(task_id, []).append({
                "success": result["success"],
                "score": result["overall_score"],
            })

    task_consistency = {}

    for task_id, runs in task_results.items():
        task_consistency[task_id] = {
            "success_rate": round(
                sum(item["success"] for item in runs) / len(runs),
                4,
            ),
            "average_score": round(
                mean(item["score"] for item in runs),
                4,
            ),
            "success_by_run": [
                item["success"] for item in runs
            ],
        }

    inconsistent_tasks = [
        task_id
        for task_id, result in task_consistency.items()
        if result["success_rate"] < 1.0
    ]

    return {
        "metrics": summary,
        "task_consistency": task_consistency,
        "inconsistent_tasks": inconsistent_tasks,
        "all_tasks_consistent": len(inconsistent_tasks) == 0,
    }


def run_repeatability_test():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fingerprints_before = get_experiment_fingerprints()

    run_reports = []

    for run_number in range(1, NUM_RUNS + 1):
        print(
            f"\n\n{'=' * 20} "
            f"REPEATABILITY RUN {run_number}/{NUM_RUNS} "
            f"{'=' * 20}"
        )

        output_path = OUTPUT_DIR / f"run_{run_number}.json"

        report = run_benchmarks(
            output_path=output_path,
            experiment_name=f"baseline_v0_run_{run_number}",
        )

        run_reports.append(report)

    fingerprints_after = get_experiment_fingerprints()

    repeatability = calculate_repeatability(run_reports)

    final_report = {
        "experiment": "baseline_v0_repeatability",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": "qwen3.5:4b",
        "num_runs": NUM_RUNS,
        "benchmark_count": len(
            json.loads(BENCHMARK_PATH.read_text())
        ),
        "fingerprints": fingerprints_before,
        "files_unchanged_during_test": (
            fingerprints_before == fingerprints_after
        ),
        "runs": [
            {
                "run": index,
                "metrics": report["metrics"],
            }
            for index, report in enumerate(run_reports, start=1)
        ],
        "repeatability": repeatability,
    }

    report_path = OUTPUT_DIR / "repeatability_report.json"

    report_path.write_text(
        json.dumps(final_report, indent=2)
    )

    print("\n========== REPEATABILITY SUMMARY ==========")
    print(json.dumps(repeatability, indent=2))

    print(f"\nFinal report saved to: {report_path}")

    return final_report


if __name__ == "__main__":
    run_repeatability_test()
