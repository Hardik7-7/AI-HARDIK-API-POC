"""
Swagger / OpenAPI parser.

Supports:
- Local file paths (.json, .yaml, .md, .txt)
- HTTP/HTTPS URLs (live swagger endpoints)

If the source is not valid JSON or YAML, it degrades gracefully and returns
the raw text content (useful for custom markdown API docs).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import requests
import yaml


def load_swagger(source: str) -> dict[str, Any]:
    """Load and parse a Swagger/OpenAPI spec from a file path or URL.

    Args:
        source: Local file path or HTTP/HTTPS URL.

    Returns:
        Parsed OpenAPI spec as a Python dict. If parsing as JSON/YAML fails,
        returns a dict with a single `_raw_text` key containing the plain text.

    Raises:
        ValueError: If the source cannot be loaded at all.
    """
    if source.startswith("http://") or source.startswith("https://"):
        return _load_from_url(source)
    return _load_from_file(source)


def _load_from_url(url: str) -> dict[str, Any]:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "yaml" in content_type or url.endswith((".yaml", ".yml")):
            return yaml.safe_load(response.text)
        return response.json()
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch from URL '{url}': {e}") from e
    except (json.JSONDecodeError, yaml.YAMLError):
        # Fallback to returning raw text for custom doc formats
        return {"_raw_text": response.text}


def _load_from_file(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise ValueError(f"Swagger file not found: '{path}'")
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            
        if file_path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(content)
        return json.loads(content)
    except (json.JSONDecodeError, yaml.YAMLError):
        # Fallback to returning raw text for custom doc formats (.md, .txt)
        return {"_raw_text": content}


def swagger_to_text(spec: dict[str, Any]) -> str:
    """Convert a parsed OpenAPI spec to a compact text representation for LLM prompts.

    If it's our raw fallback format, return the text directly.
    Otherwise serialize to JSON for maximum compatibility with LLM tokenizers.
    """
    if "_raw_text" in spec and len(spec) == 1:
        return spec["_raw_text"]
    return json.dumps(spec, indent=2)
