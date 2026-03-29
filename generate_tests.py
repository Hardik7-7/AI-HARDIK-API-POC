"""
Phase 2 CLI — Generate Test Code.

Usage:
  python generate_tests.py

Run this AFTER reviewing JSON scenario files in output/scenarios/ from Phase 1.
After running, optionally execute Phase 3:
  python run_and_heal.py
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
        prog="generate_tests",
        description=(
            "Phase 2: Convert reviewed test cases JSON into runnable pytest code.\n"
            "Run AFTER reviewing JSON files in output/scenarios/ from Phase 1."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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

    console.print()
    console.print("[bold]AI Backend Test Automation — Phase 2: Test Code Generation[/bold]")
    console.print(f"  Skill      : {args.skill}")
    console.print()

    try:
        from src.generators.code_generator import generate_tests
        from pathlib import Path

        scenario_dir = Path("output/scenarios")
        output_dir = "output/tests"
        
        if not scenario_dir.exists():
            console.print("[yellow]No 'output/scenarios' directory found. Run Phase 1 first.[/yellow]")
            sys.exit(0)

        target_json = scenario_dir / "all_scenarios.json"
        if not target_json.exists():
            console.print("[yellow]No 'output/scenarios/all_scenarios.json' found. Run Phase 1 first.[/yellow]")
            sys.exit(0)

        generate_tests(
            test_cases_path=str(target_json),
            skill_path=args.skill,
            output_dir=output_dir,
        )

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
