
import re
from decimal import Decimal, InvalidOperation


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
            numbers.append(Decimal(match.replace(",", "")))
        except InvalidOperation:
            continue

    return numbers


def evaluate_tools(policy: dict, actual_tools: list[str]) -> dict:
    """Measure whether the tools used satisfy a task's tool policy.

    ``required`` tools must all be used, ``optional`` tools may be used, and
    ``forbidden`` tools must not be used. Any used tool not listed in one of
    those groups is treated as unexpected. Inputs are converted to sets, so
    repeated calls to the same tool count once in these measurements.

    The result contains:
    - ``compliant``: true only when no required tool is missing and no
      forbidden or unexpected tool was used.
    - ``precision``: the fraction of distinct used tools that are allowed
      (required or optional). With no used tools, this is ``1.0`` if no tools
      are required, otherwise ``0.0``.
    - ``recall``: the fraction of required tools that were used, or ``1.0``
      when the policy has no required tools.
    - ``missing``, ``forbidden_used``, and ``unexpected``: sorted lists of
      required tools not used, forbidden tools used, and unclassified tools
      used, respectively.
    """

    required = set(policy.get("required", []))
    optional = set(policy.get("optional", []))
    forbidden = set(policy.get("forbidden", []))
    actual = set(actual_tools)

    allowed = required | optional

    missing = required - actual
    forbidden_used = forbidden & actual
    unexpected = actual - allowed - forbidden

    tool_precision = (
        len(actual & allowed) / len(actual)
        if actual else (0.0 if required else 1.0)
    )

    tool_recall = (
        len(required & actual) / len(required)
        if required else 1.0
    )

    compliant = (
        not missing
        and not forbidden_used
        and not unexpected
    )

    return {
        "compliant": compliant,
        "precision": round(tool_precision, 3),
        "recall": round(tool_recall, 3),
        "missing": sorted(missing),
        "forbidden_used": sorted(forbidden_used),
        "unexpected": sorted(unexpected),
    }


def evaluate_task(
    task: dict,
    output: str,
    actual_tools: list[str],
) -> dict:
    """Score one agent response against its benchmark task.

    Tool usage is evaluated by ``evaluate_tools`` using the task's
    ``tool_policy``. Required answer terms are matched case-insensitively as
    substrings of the output, and expected numbers are matched against
    numbers extracted from the output.

    ``answer_score`` and ``number_score`` are the fractions of required terms
    and expected numbers matched, respectively; each defaults to ``1.0`` when
    its expectation list is empty. Their mean forms ``content_score``.
    ``overall_score`` weights tool-policy compliance at 40% and content at
    60%, and ``success`` is true when that score is at least ``0.8``.

    The returned dictionary includes these scores, the matched terms and
    numbers, tool-policy diagnostics, the distinct tools used, and the
    original task and output identifiers/details.
    """

    # Tool evaluation
    tool_result = evaluate_tools(
        task.get("tool_policy", {}),
        actual_tools,
    )

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

    matched_numbers = [
        expected
        for expected in expected_numbers
        if Decimal(expected) in actual_numbers
    ]

    number_score = (
        len(matched_numbers) / len(expected_numbers)
        if expected_numbers else 1.0
    )

    # Combined scoring
    content_score = (answer_score + number_score) / 2

    overall_score = (
        0.4 * float(tool_result["compliant"])
        + 0.6 * content_score
    )

    return {
        "task_id": task["id"],
        "category": task["category"],

        "tool_correct": tool_result["compliant"],
        "tool_precision": tool_result["precision"],
        "tool_recall": tool_result["recall"],
        "tool_evaluation": tool_result,

        "answer_score": round(answer_score, 3),
        "number_score": round(number_score, 3),

        "overall_score": round(overall_score, 3),
        "success": overall_score >= 0.8,

        "matched_terms": matched_terms,
        "matched_numbers": matched_numbers,
        "actual_numbers": [str(n) for n in actual_numbers],

        "tool_policy": task.get("tool_policy", {}),
        "actual_tools": sorted(set(actual_tools)),

        "output": output,
    }
