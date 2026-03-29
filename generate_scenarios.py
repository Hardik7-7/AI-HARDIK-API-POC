"""
Phase 1 CLI — Generate Test Scenarios.

Usage:
  python generate_scenarios.py --swagger inputs/swagger/my_api.json --story inputs/stories/my_story.md
  python generate_scenarios.py --swagger https://api.example.com/swagger.json --story inputs/stories/my_story.md

After running, review the generated JSON in output/scenarios/, then run:
  python generate_tests.py
"""
from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate_scenarios",
        description=(
            "Phase 1: Use LLM to map APIs and generate test case scenarios.\n"
            "Output: output/test_cases.json (review before running Phase 2)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--swagger", "-s",
        required=True,
        metavar="PATH_OR_URL",
        help="Path to Swagger/OpenAPI file (.json or .yaml) or live HTTP URL.",
    )
    parser.add_argument(
        "--story", "-t",
        required=True,
        metavar="PATH",
        help="Path to the user story file (.md or .txt).",
    )
    parser.add_argument(
        "--skill",
        default="skills/api_testing_skill.md",
        metavar="PATH",
        help="Path to the skill file (default: skills/api_testing_skill.md).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        from src.generators.scenario_generator import generate_scenarios
        from src.parsers.swagger_parser import load_swagger, swagger_to_text
        from pathlib import Path

        story_stem = Path(args.story).stem
        output_path = f"output/scenarios/{story_stem}.json"

        console.print()
        console.print("[bold]AI Backend Test Automation — Phase 1: Scenario Generation[/bold]")
        console.print(f"  Swagger : {args.swagger}")
        console.print(f"  Story   : {args.story}")
        console.print(f"  Skill   : {args.skill}")
        console.print(f"  Output  : {output_path}")
        console.print()

        # Load the API documentation
        swagger_spec = load_swagger(args.swagger)
        api_text = swagger_to_text(swagger_spec)

        generate_scenarios(
            api_spec=api_text,
            story_path=args.story,
            skill_path=args.skill,
            output_path=output_path,
        )

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
