
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
    """Score tool use and answer content against a task's expectations.

    The returned metrics mean:
    - ``tool_correct``: all expected tools were used and no unexpected tools
      were used.
    - ``tool_precision``: the fraction of distinct tools used that were
      expected; ``0.0`` when no tools were used.
    - ``tool_recall``: the fraction of expected tools that were used; ``1.0``
      when the task expects no tools.
    - ``answer_score``: the fraction of required terms found in the output,
      ignoring case; ``1.0`` when no terms are required.
    - ``number_score``: the fraction of expected numbers present among the
      numbers extracted from the output; ``1.0`` when no numbers are expected.
    - ``overall_score``: a weighted score with tool correctness contributing
      40% and the mean of answer and number scores contributing 60%.
    - ``success``: whether the overall score is at least ``0.8``.

    The result also includes the matched and expected values, the extracted
    numbers, and the original task/output details for inspection.
    """

    # Tool selection
    expected_tools = set(task["expected_tools"])
    actual_tools = set(actual_tools)

    required_tools_used = expected_tools.issubset(actual_tools)

    unexpected_tools = actual_tools - expected_tools

    tool_precision = (
        len(expected_tools & actual_tools) / len(actual_tools)
        if actual_tools else 0.0
    )

    tool_recall = (
        len(expected_tools & actual_tools) / len(expected_tools)
        if expected_tools else 1.0
    )

    tool_correct = required_tools_used and not unexpected_tools

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
        "tool_precision": round(tool_precision, 3),
        "tool_recall": round(tool_recall, 3),
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
