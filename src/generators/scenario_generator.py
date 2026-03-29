"""
Scenario Generator — Phase 1.

Takes the user story, the LLM-mapped API endpoints, and the skill file
to generate a structured list of test cases in JSON format.

Output: output/test_cases.json  ← Human reviews and edits this before Phase 2.
"""
from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel

from src.llm.client import call_llm
from src.llm.prompt_builder import SkillFile
from src.parsers.story_parser import load_story
from src.utils.file_io import extract_json_from_llm_response, write_json
from src.utils.validators import validate_test_cases, ValidationError

console = Console()


def generate_scenarios(
    api_spec: str,
    story_path: str,
    skill_path: str = "skills/api_testing_skill.md",
    output_path: str = "output/test_cases.json",
) -> list[dict[str, Any]]:
    """Generate test cases (JSON) from an API specification and a user story.

    Args:
        api_spec: Raw text / JSON of the API documentation.
        story_path: Path to the user story file.
        skill_path: Path to the skill .md file.
        output_path: Where to write the generated test cases JSON.

    Returns:
        List of validated test case dicts.
    """
    console.rule("[bold magenta]Scenario Generation (Phase 1)[/bold magenta]")

    # 1. Load user story
    console.print("[cyan]Loading user story...[/cyan]")
    story_text = load_story(story_path)

    # 2. Build prompt
    console.print("[cyan]Building scenario generation prompt...[/cyan]")
    skill = SkillFile(skill_path)
    prompt = skill.build_prompt(
        "scenario_generation",
        USER_STORY=story_text,
        API_DOCUMENTATION=api_spec,
    )

    # 3. Call LLM
    console.print("[yellow]Calling LLM to generate test scenarios...[/yellow]")
    raw_response = call_llm(prompt, expect_json=True)

    # 4. Parse response
    console.print("[cyan]Parsing response...[/cyan]")
    try:
        test_cases = extract_json_from_llm_response(raw_response)
    except ValueError as e:
        console.print(f"[red]Failed to parse LLM response as JSON:[/red]\n{e}")
        _save_raw_response(raw_response, output_path)
        raise

    # 5. Validate schema
    console.print("[cyan]Validating test case schema...[/cyan]")
    try:
        test_cases = validate_test_cases(test_cases)
    except ValidationError as e:
        console.print(f"[red]Validation failed:[/red]\n{e}")
        console.print(
            "[yellow]Saving raw (invalid) test cases for manual inspection...[/yellow]"
        )
        write_json(output_path.replace(".json", "_raw.json"), test_cases)
        raise

    # 6. Save and report
    write_json(output_path, test_cases)

    console.print()
    console.print(
        Panel(
            f"[green bold]✓ Generated {len(test_cases)} test case(s)[/green bold]\n\n"
            + "\n".join(
                f"  [{tc.get('priority','?'):6}] [bold]{tc.get('id','?')}[/bold]  {tc.get('title','')}"
                for tc in test_cases
            )
            + f"\n\n[dim]→ Review and edit: [bold]{output_path}[/bold][/dim]\n"
            + "[dim]→ Then run: [bold]python generate_tests.py[/bold][/dim]",
            title="Phase 1 Complete",
            border_style="green",
        )
    )

    return test_cases


def _save_raw_response(raw: str, output_path: str) -> None:
    """Save raw LLM response for debugging when JSON parsing fails."""
    raw_path = output_path.replace(".json", "_llm_raw.txt")
    from src.utils.file_io import write_text
    write_text(raw_path, raw)
    console.print(f"[dim]Raw LLM response saved to: {raw_path}[/dim]")
