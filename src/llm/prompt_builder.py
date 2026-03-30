"""
Prompt builder — reads the skill .md file and fills in {{PLACEHOLDER}} variables.

The skill file uses a simple convention:
  ### PROMPT_START: <name>
  ...prompt content with {{PLACEHOLDERS}}...
  ### PROMPT_END: <name>

Sections are extracted by name and placeholders are replaced at runtime.
"""
from __future__ import annotations

import re
from pathlib import Path


_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")
_SECTION_RE = re.compile(
    r"###\s+PROMPT_START:\s+(\w+)\s*\n(.*?)###\s+PROMPT_END:\s+\1",
    re.DOTALL,
)
_PRODUCT_CONTEXT_RE = re.compile(
    r"## SECTION: Product Context\s*\n(.*?)(?=\n## SECTION:)",
    re.DOTALL,
)
_TEST_CASE_FORMAT_RE = re.compile(
    r"## SECTION: Test Case JSON Format\s*\n(.*?)(?=\n## SECTION:)",
    re.DOTALL,
)


class SkillFile:
    """Parsed representation of a skill .md file."""

    def __init__(self, path: str = "skills/api_testing_skill.md") -> None:
        skill_path = Path(path)
        if not skill_path.exists():
            raise ValueError(f"Skill file not found: '{path}'")
        self._content = skill_path.read_text(encoding="utf-8")
        self._prompts = self._extract_prompts()
        self.product_context = self._extract_product_context()
        self.test_case_format = self._extract_test_case_format()

    # ── Extraction ─────────────────────────────────────────────────────────────

    def _extract_prompts(self) -> dict[str, str]:
        return {
            name: body.strip()
            for name, body in _SECTION_RE.findall(self._content)
        }

    def _extract_product_context(self) -> str:
        m = _PRODUCT_CONTEXT_RE.search(self._content)
        return m.group(1).strip() if m else ""

    def _extract_test_case_format(self) -> str:
        m = _TEST_CASE_FORMAT_RE.search(self._content)
        return m.group(1).strip() if m else ""

    # ── Public API ─────────────────────────────────────────────────────────────

    def build_prompt(self, template_name: str, **kwargs: str) -> str:
        """Get a named prompt template and fill in all {{PLACEHOLDERS}}.

        Args:
            template_name: One of: scenario_generation, code_generation, self_heal
            **kwargs: Placeholder values. Keys should match template placeholders (case-sensitive).

        Returns:
            Fully resolved prompt string ready to send to the LLM.

        Raises:
            ValueError: If template_name is not found in the skill file.
        """
        if template_name not in self._prompts:
            available = list(self._prompts.keys())
            raise ValueError(
                f"Prompt template '{template_name}' not found in skill file. "
                f"Available: {available}"
            )

        # Always inject product_context and test_case_format
        context = {
            "PRODUCT_CONTEXT": self.product_context,
            "TEST_CASE_FORMAT": self.test_case_format,
            **kwargs,
        }

        prompt = self._prompts[template_name]
        missing = []
        for match in _PLACEHOLDER_RE.finditer(prompt):
            key = match.group(1)
            if key not in context:
                missing.append(key)

        if missing:
            raise ValueError(
                f"Missing placeholder values for prompt '{template_name}': {missing}"
            )

        for key, value in context.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", value)

        return prompt

    def list_templates(self) -> list[str]:
        return list(self._prompts.keys())
