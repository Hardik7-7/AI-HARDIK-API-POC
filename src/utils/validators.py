"""
Test case JSON schema validator.

Validates that each test case in the generated JSON has the required fields
and correct types before it gets written to output or sent for code generation.
"""
from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = {"id", "title", "description", "tags", "priority", "steps"}
REQUIRED_STEP_FIELDS = {"step", "action", "request", "expected"}
VALID_PRIORITIES = {"high", "medium", "low"}
VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


class ValidationError(Exception):
    pass


def validate_test_cases(test_cases: Any) -> list[dict]:
    """Validate a list of test case dicts.

    Args:
        test_cases: The parsed JSON value (should be a list).

    Returns:
        The validated list (unchanged).

    Raises:
        ValidationError: With a descriptive message if validation fails.
    """
    if not isinstance(test_cases, list):
        raise ValidationError(
            f"Expected a JSON array of test cases, got: {type(test_cases).__name__}"
        )
    if len(test_cases) == 0:
        raise ValidationError("Test case list is empty — the LLM returned no test cases.")

    errors = []
    for i, tc in enumerate(test_cases):
        tc_id = tc.get("id", f"[index {i}]")
        tc_errors = _validate_test_case(tc, tc_id)
        errors.extend(tc_errors)

    if errors:
        formatted = "\n".join(f"  - {e}" for e in errors)
        raise ValidationError(
            f"Test case validation failed with {len(errors)} error(s):\n{formatted}"
        )

    return test_cases


def _validate_test_case(tc: Any, tc_id: str) -> list[str]:
    errors = []

    if not isinstance(tc, dict):
        return [f"{tc_id}: Expected object, got {type(tc).__name__}"]

    # Check required fields
    missing = REQUIRED_FIELDS - set(tc.keys())
    if missing:
        errors.append(f"{tc_id}: Missing required fields: {sorted(missing)}")

    # Validate priority
    if "priority" in tc and tc["priority"] not in VALID_PRIORITIES:
        errors.append(
            f"{tc_id}: Invalid priority '{tc['priority']}'. "
            f"Must be one of: {VALID_PRIORITIES}"
        )

    # Validate tags
    if "tags" in tc and not isinstance(tc["tags"], list):
        errors.append(f"{tc_id}: 'tags' must be a list")

    # Validate steps
    if "steps" in tc:
        if not isinstance(tc["steps"], list) or len(tc["steps"]) == 0:
            errors.append(f"{tc_id}: 'steps' must be a non-empty list")
        else:
            for step in tc["steps"]:
                errors.extend(_validate_step(step, tc_id))

    return errors


def _validate_step(step: Any, tc_id: str) -> list[str]:
    errors = []
    if not isinstance(step, dict):
        return [f"{tc_id} step: Expected object, got {type(step).__name__}"]

    missing = REQUIRED_STEP_FIELDS - set(step.keys())
    if missing:
        errors.append(f"{tc_id} step {step.get('step', '?')}: Missing fields: {sorted(missing)}")

    if "request" in step and isinstance(step["request"], dict):
        method = step["request"].get("method", "").upper()
        if method and method not in VALID_METHODS:
            errors.append(
                f"{tc_id} step {step.get('step', '?')}: "
                f"Invalid HTTP method '{method}'"
            )

    return errors
