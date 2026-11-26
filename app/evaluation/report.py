
import json
from pathlib import Path


def generate_report():

    path = Path("artifacts/baseline_results.json")
    report = json.loads(path.read_text())

    metrics = report["metrics"]

    lines = [
        "# Baseline Evaluation Report",
        "",
        f"Model: {report['model']}",
        f"Total tasks: {metrics['total_tasks']}",
        "",
        "## Overall Metrics",
        "",
        f"- Success rate: {metrics['success_rate']:.1%}",
        f"- Tool accuracy: {metrics['tool_accuracy']:.1%}",
        f"- Average score: {metrics['average_score']:.3f}",
        f"- Successful tasks: {metrics['successful_tasks']}",
        f"- Failed tasks: {metrics['failed_tasks']}",
        "",
        "## Category Breakdown",
        "",
        "| Category | Tasks | Success rate | Average score |",
        "|---|---:|---:|---:|",
    ]

    for category, values in metrics["categories"].items():
        lines.append(
            f"| {category} | {values['total']} | "
            f"{values['success_rate']:.1%} | "
            f"{values['average_score']:.3f} |"
        )

    lines.extend([
        "",
        "## Failed Tasks",
        "",
    ])

    for result in report["results"]:
        if not result["success"]:
            lines.append(
                f"- **{result['task_id']}**: "
                f"Score {result['overall_score']:.2f}"
            )

    Path("artifacts/baseline_report.md").write_text(
        "\n".join(lines)
    )

    print("Report generated: artifacts/baseline_report.md")


if __name__ == "__main__":
    generate_report()
