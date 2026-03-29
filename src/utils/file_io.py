"""
File I/O helpers — reading and writing JSON, text, and Python files.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def read_json(path: str) -> Any:
    """Read and parse a JSON file."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: '{path}'")
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: Any, indent: int = 2) -> None:
    """Write data to a JSON file, creating parent directories if needed."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def read_text(path: str) -> str:
    """Read a text file and return its content."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Text file not found: '{path}'")
    return file_path.read_text(encoding="utf-8")


def write_text(path: str, content: str) -> None:
    """Write text to a file, creating parent directories if needed."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def extract_json_from_llm_response(response: str) -> Any:
    """Attempt to extract JSON from an LLM response.

    LLMs sometimes wrap JSON in markdown code fences — this handles that.

    Args:
        response: Raw LLM response string.

    Returns:
        Parsed JSON object (dict or list).

    Raises:
        ValueError: If no valid JSON can be extracted.
    """
    # Try parsing directly first
    stripped = response.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fences (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*\n([\s\S]*?)\n```", stripped)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding the first [ or { and last ] or }
    start = min(
        (stripped.find(c) for c in ("[", "{") if stripped.find(c) != -1),
        default=-1,
    )
    if start != -1:
        end = max(stripped.rfind("]"), stripped.rfind("}"))
        if end > start:
            try:
                return json.loads(stripped[start : end + 1])
            except json.JSONDecodeError:
                pass

    raise ValueError(
        "Could not extract valid JSON from LLM response. "
        "Check the skill file prompt instructions."
    )


def extract_code_from_llm_response(response: str) -> str:
    """Extract Python code from an LLM response.

    Strips markdown code fences if present.

    Args:
        response: Raw LLM response string.

    Returns:
        Clean Python code string.
    """
    stripped = response.strip()
    # Remove markdown code fences
    fence_match = re.search(r"```(?:python)?\s*\n([\s\S]*?)```", stripped)
    if fence_match:
        return fence_match.group(1).strip()
    
    # Fallback manual strip if regex misses some edge case
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
        
    return stripped
