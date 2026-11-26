
import json
from pathlib import Path
from collections import defaultdict

from app.evaluation.runner import run_benchmarks


def run_repeatability(experiments=3):

    experiment_results = []

    for iteration in range(experiments):
        print(f"\n========== RUN {iteration + 1} ==========")

        report = run_benchmarks()

        experiment_results.append(report)

    task_scores = defaultdict(list)

    for report in experiment_results:
        for result in report["results"]:
            task_scores[result["task_id"]].append(
                result["overall_score"]
            )

    stability = {}

    for task_id, scores in task_scores.items():
        stability[task_id] = {
            "scores": scores,
            "mean": round(sum(scores) / len(scores), 3),
            "min": min(scores),
            "max": max(scores),
            "consistent": len(set(scores)) == 1
        }

    output = {
        "runs": experiments,
        "task_stability": stability
    }

    Path("artifacts").mkdir(exist_ok=True)

    Path("artifacts/repeatability.json").write_text(
        json.dumps(output, indent=2)
    )

    print("\nRepeatability results saved.")

    return output


if __name__ == "__main__":
    run_repeatability()
