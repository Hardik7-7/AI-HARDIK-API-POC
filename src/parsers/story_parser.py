"""
User story parser.

Reads a user story from a .md or .txt file and returns the raw text.
"""
from __future__ import annotations

from pathlib import Path


def load_story(path: str) -> str:
    """Load a user story from a text or markdown file.

    Args:
        path: Path to the .md or .txt file.

    Returns:
        Raw text content of the user story.

    Raises:
        ValueError: If the file does not exist or cannot be read.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise ValueError(f"User story file not found: '{path}'")
    if file_path.suffix not in (".md", ".txt", ".markdown"):
        raise ValueError(
            f"Unsupported user story file format '{file_path.suffix}'. "
            "Use .md, .txt, or .markdown."
        )
    return file_path.read_text(encoding="utf-8").strip()
