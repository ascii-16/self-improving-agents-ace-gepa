
import re


def normalize(text: str) -> str:
    return re.sub(r"[\s,]", "", text.lower())


def contains_number(output: str, number: str) -> bool:
    normalized = output.replace(",", "")
    pattern = rf"(?<![\d.]){re.escape(number)}(?![\d.])"
    return re.search(pattern, normalized) is not None


def evaluate_task(
    task: dict,
    output: str,
    actual_tools: list[str],
) -> dict:

    expected_tools = set(task["expected_tools"])
    actual_tools = set(actual_tools)

    # Tool selection
    tool_correct = expected_tools == actual_tools

    # Required answer terms
    normalized_output = output.lower()

    required_terms = task.get("required_terms", [])

    matched_terms = [
        term for term in required_terms
        if term.lower() in normalized_output
    ]

    answer_score = (
        len(matched_terms) / len(required_terms)
        if required_terms else 1.0
    )

    # Numeric correctness
    expected_numbers = task.get("expected_numbers", [])

    normalized = normalize(output)

    matched_numbers = [
        number for number in expected_numbers
        if contains_number(output, number)
    ]

    number_score = (
        len(matched_numbers) / len(expected_numbers)
        if expected_numbers else 1.0
    )

    # Combine semantic and numeric checks
    content_score = (answer_score + number_score) / 2

    overall_score = (
        0.4 * float(tool_correct)
        + 0.6 * content_score
    )

    return {
        "task_id": task["id"],
        "category": task["category"],
        "tool_correct": tool_correct,
        "answer_score": answer_score,
        "number_score": number_score,
        "overall_score": round(overall_score, 3),
        "success": overall_score >= 0.8,
        "matched_terms": matched_terms,
        "matched_numbers": matched_numbers,
        "expected_tools": sorted(expected_tools),
        "actual_tools": sorted(actual_tools),
        "output": output,
    }
