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
    test_cases_path: str = "output/scenarios/all_scenarios.json",
    skill_path: str = "skills/api_testing_skill.md",
    output_dir: str = "output/tests",
    target_story: str | None = None,
) -> list[str]:
    """Generate pytest code from grouped JSON scenarios.

    Args:
        test_cases_path: Path to the grouped all_scenarios.json file.
        skill_path: Path to the skill .md file.
        output_dir: Directory to write generated test files.
        target_story: If provided, only generate tests for this specific story stem.

    Returns:
        List of paths to the generated test files.
    """
    console.rule("[bold blue]Test Code Generation (Phase 2)[/bold blue]")

    # 1. Load test cases
    console.print(f"[cyan]Loading test cases from: {test_cases_path}[/cyan]")
    scenarios_data = read_json(test_cases_path)
    if not isinstance(scenarios_data, list) or not scenarios_data:
        raise ValueError(f"'{test_cases_path}' must be a non-empty JSON array.")
        
    if "story" not in scenarios_data[0]:
        raise ValueError(
            f"'{test_cases_path}' appears to be the old flat format. "
            "Please regenerate scenarios using Phase 1 to get the grouped format."
        )

    console.print(f"[dim]Loaded {len(scenarios_data)} scenario group(s)[/dim]")

    skill = SkillFile(skill_path)
    generated_files = []

    for story_group in scenarios_data:
        story_name = story_group["story"]
        
        if target_story and story_name != target_story:
            continue
            
        test_cases = story_group["test_cases"]
        
        console.print(f"\n[bold blue]Generating tests for story: {story_name}[/bold blue]")

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
            console.print(f"[bold red]LLM returned empty response for '{story_name}'. Writing empty file anyway for healer to catch.[/bold red]")

        try:
            ast.parse(code)
        except SyntaxError as e:
            console.print(f"[bold yellow]Warning: Generated code is not valid Python for '{story_name}' (possibly truncated): {e}. Writing anyway for healer to catch.[/bold yellow]")

        output_path = Path(output_dir) / f"test_{story_name}.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_text(str(output_path), code)
        console.print(f"[green]✓ Test file generated: {output_path}[/green]")
        generated_files.append(str(output_path))

    console.print()
    console.print(
        Panel(
            f"[green bold]✓ Phase 2 Complete[/green bold]\n\n"
            f"[dim]Generated {len(generated_files)} test file(s)\n"
            "→ Review the generated code before running\n"
            "→ Set BASE_URL and AUTH_TOKEN env vars\n"
            f"→ Then run: [bold]python run_and_heal.py --test-dir {output_dir}[/bold][/dim]",
            title="Phase 2 Complete",
            border_style="blue",
        )
    )

    return generated_files

