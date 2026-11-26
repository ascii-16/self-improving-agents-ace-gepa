
import re
from decimal import Decimal, InvalidOperation


def normalize(text: str) -> str:
    return re.sub(r"[\s,]", "", text.lower())


def extract_numbers(text: str) -> list[Decimal]:
    """Extract numeric values from text."""

    pattern = (
        r"(?<![\w.])"
        r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
        r"(?![\w.])"
    )

    numbers = []

    for match in re.findall(pattern, text):
        try:
            numbers.append(
                Decimal(match.replace(",", ""))
            )
        except InvalidOperation:
            continue

    return numbers


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

    actual_numbers = extract_numbers(output)

    matched_numbers = []

    for expected in expected_numbers:
        if Decimal(expected) in actual_numbers:
            matched_numbers.append(expected)

    number_score = (
        len(matched_numbers) / len(expected_numbers)
        if expected_numbers else 1.0
    )

    # Combine scores
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
        "actual_numbers": [str(n) for n in actual_numbers],
        "expected_tools": sorted(expected_tools),
        "actual_tools": sorted(actual_tools),
        "output": output,
    }
