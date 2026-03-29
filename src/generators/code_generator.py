"""
Code Generator — Phase 2.

Reads the human-reviewed test_cases.json and generates runnable pytest code.
Phase 2 is completely independent of Phase 1 inputs (no swagger, no story needed).
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

from src.llm.client import call_llm
from src.llm.prompt_builder import SkillFile
from src.utils.file_io import extract_code_from_llm_response, read_json, write_text

console = Console()


def generate_tests(
    test_cases_path: str = "output/test_cases.json",
    skill_path: str = "skills/api_testing_skill.md",
    output_dir: str = "output/tests",
) -> str:
    """Generate pytest code from reviewed test cases JSON.

    Args:
        test_cases_path: Path to the reviewed test_cases.json file.
        skill_path: Path to the skill .md file.
        output_dir: Directory to write generated test files.

    Returns:
        Path to the generated test file.
    """
    console.rule("[bold blue]Test Code Generation (Phase 2)[/bold blue]")

    # 1. Load test cases
    console.print(f"[cyan]Loading test cases from: {test_cases_path}[/cyan]")
    test_cases: list[dict[str, Any]] = read_json(test_cases_path)
    if not isinstance(test_cases, list) or not test_cases:
        raise ValueError(f"'{test_cases_path}' must be a non-empty JSON array.")
    console.print(f"[dim]Loaded {len(test_cases)} test case(s)[/dim]")

    skill = SkillFile(skill_path)

    # 3. Build prompt
    console.print("[cyan]Building code generation prompt...[/cyan]")
    test_cases_text = json.dumps(test_cases, indent=2)
    prompt = skill.build_prompt(
        "code_generation",
        TEST_CASES_JSON=test_cases_text,
    )

    # 4. Call LLM
    console.print("[yellow]Calling LLM to generate pytest code...[/yellow]")
    raw_response = call_llm(prompt)

    # 5. Extract the test code and write to disk
    console.print("[cyan]Extracting Python code from response...[/cyan]")
    code = extract_code_from_llm_response(raw_response)

    if not code.strip():
        raise RuntimeError(
            "LLM returned an empty response for code generation. "
            "The test file was NOT written. "
            "Check the LLM output above for finish_reason details. "
            "Try increasing LLM_MAX_TOKENS in your .env (e.g. LLM_MAX_TOKENS=16000)."
        )

    # Validate that the generated code is syntactically valid Python.
    # A SyntaxError here means the output was truncated or malformed.
    try:
        ast.parse(code)
    except SyntaxError as e:
        raise RuntimeError(
            f"Generated code is not valid Python (likely truncated by LLM): {e}\n"
            "The test file was NOT written. "
            "Try increasing LLM_MAX_TOKENS in your .env or re-running to trigger a retry."
        ) from e

    stem = Path(test_cases_path).stem
    output_path = Path(output_dir) / f"test_{stem}.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(str(output_path), code)

    console.print()
    console.print(
        Panel(
            f"[green bold]✓ Test file generated[/green bold]\n\n"
            f"  [bold]{output_path}[/bold]\n\n"
            "[dim]→ Review the generated code before running\n"
            "→ Set BASE_URL and AUTH_TOKEN env vars\n"
            f"→ Then run: [bold]python run_and_heal.py --test-dir {output_dir}[/bold][/dim]",
            title="Phase 2 Complete",
            border_style="blue",
        )
    )

    return str(output_path)

