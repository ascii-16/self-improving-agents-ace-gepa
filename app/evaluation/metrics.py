
from collections import defaultdict


def calculate_metrics(results: list[dict]) -> dict:

    if not results:
        return {"total_tasks": 0, "success_rate": 0}

    total = len(results)

    successful = sum(
        result["success"] for result in results
    )

    tool_correct = sum(
        result["tool_correct"] for result in results
    )

    average_score = sum(
        result["overall_score"] for result in results
    ) / total

    categories = defaultdict(list)

    for result in results:
        categories[result["category"]].append(result)

    category_metrics = {}

    for category, items in categories.items():
        category_metrics[category] = {
            "total": len(items),
            "success_rate": round(
                sum(item["success"] for item in items)
                / len(items), 3
            ),
            "average_score": round(
                sum(item["overall_score"] for item in items)
                / len(items), 3
            ),
        }

    return {
        "total_tasks": total,
        "successful_tasks": successful,
        "failed_tasks": total - successful,
        "success_rate": round(successful / total, 3),
        "tool_accuracy": round(tool_correct / total, 3),
        "average_score": round(average_score, 3),
        "categories": category_metrics,
    }
