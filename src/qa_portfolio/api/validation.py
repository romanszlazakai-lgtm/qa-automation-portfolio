"""Schema validation helper with readable failure messages."""

from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


def assert_matches_schema(instance: Any, schema: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        details = "\n".join(f"  {list(e.path)}: {e.message}" for e in errors)
        raise AssertionError(f"Response does not match schema:\n{details}")
