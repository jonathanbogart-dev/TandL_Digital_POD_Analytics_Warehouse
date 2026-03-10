"""Parse .js dataset files of the form:

    window.IDENTIFIER = [ ... ];

The embedded value must be a valid JSON array (double-quoted strings,
no trailing commas, no inline JS comments inside the array body).
"""

import json
import re
from typing import Any

# Matches the assignment token, e.g. "window.DATASET = "
_ASSIGNMENT = re.compile(r"window\.[A-Za-z_]\w*\s*=\s*", re.DOTALL)


def parse_js_dataset(content: str) -> list[dict[str, Any]]:
    """Extract and return the JSON array assigned to window.IDENTIFIER.

    Args:
        content: Full text of a .js file.

    Returns:
        List of record dicts parsed from the embedded JSON array.

    Raises:
        ValueError: If no window assignment is found, the value is not an
            array/object, or the array is not valid JSON.
    """
    m = _ASSIGNMENT.search(content)
    if not m:
        raise ValueError(
            "No 'window.IDENTIFIER = ...' assignment found in file."
        )

    tail = content[m.end():].lstrip()
    if not tail or tail[0] not in ("[", "{"):
        raise ValueError(
            f"Expected '[' or '{{' after assignment, got: {tail[:40]!r}"
        )

    json_str = _extract_balanced(tail)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Embedded value is not valid JSON: {exc}") from exc

    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError(
        f"Expected a JSON array or object, got {type(data).__name__}."
    )


def _extract_balanced(text: str) -> str:
    """Return the first balanced JSON value (array or object) from *text*.

    Handles nested brackets and string literals with escaped characters.
    Stops at the first character after the matching close bracket.

    Raises:
        ValueError: If brackets are unbalanced.
    """
    open_ch = text[0]
    close_ch = "]" if open_ch == "[" else "}"
    depth = 0
    in_str = False
    escape = False

    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_str:
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[: i + 1]

    raise ValueError("Unbalanced brackets — could not find end of JSON value.")
