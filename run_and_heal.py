"""
Phase 3 CLI — Run Tests with Self-Healing.

Usage:
  python run_and_heal.py
  python run_and_heal.py --test-dir output/tests --max-attempts 5

Run this AFTER Phase 2 generates test code.
Tests are run, failures analyzed by LLM, code is fixed, and tests are re-run automatically.
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
        prog="run_and_heal",
        description=(
            "Phase 3: Run generated tests and auto-heal failures using LLM.\n"
            "Run AFTER Phase 2 generates test code."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--test-dir", "-d",
        default="output/tests",
        metavar="DIR",
        help="Directory containing generated test files (default: output/tests).",
    )
    parser.add_argument(
        "--test-file", "-f",
        default=None,
        metavar="FILE",
        help="Test file to target for healing (default: processes all test_*.py in test-dir).",
    )
    parser.add_argument(
        "--skill",
        default="skills/api_testing_skill.md",
        metavar="PATH",
        help="Path to the skill file (default: skills/api_testing_skill.md).",
    )
    parser.add_argument(
        "--max-attempts", "-n",
        type=int,
        default=None,
        metavar="N",
        help="Max heal attempts (default: from SELF_HEAL_MAX_ATTEMPTS env var or 3).",
    )
    parser.add_argument(
        "--report-dir",
        default="output/reports",
        metavar="DIR",
        help="Directory for pytest HTML reports (default: output/reports).",
    )
    parser.add_argument(
        "--no-heal",
        action="store_true",
        help="Run tests once without attempting any auto-healing (dry run).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    console.print()
    console.print("[bold]AI Backend Test Automation — Phase 3: Run & Self-Heal[/bold]")
    console.print(f"  Test Dir     : {args.test_dir}")
    console.print(f"  Test File    : {args.test_file}")
    console.print(f"  Max Attempts : {args.max_attempts or 'from env (default 3)'}")
    console.print(f"  Self-Heal    : {'disabled (--no-heal)' if args.no_heal else 'enabled'}")
    console.print()

    try:
        from src.generators.self_healer import run_and_heal
        from pathlib import Path

        if args.test_file:
            test_files = [args.test_file]
        else:
            test_files = [f.name for f in Path(args.test_dir).glob("test_*.py")]

        if not test_files:
            console.print(f"[yellow]No test files found in {args.test_dir}. Run Phase 2 first.[/yellow]")
            sys.exit(0)

        all_success = True

        for t_file in test_files:
            console.print(f"\n[bold magenta]► Processing {t_file}[/bold magenta]")
            
            if args.no_heal:
                # Run once, no healing
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(Path(args.test_dir) / t_file), "-v", "--tb=short"],
                    cwd=".",
                )
                if result.returncode != 0:
                    all_success = False
            else:
                success = run_and_heal(
                    test_dir=args.test_dir,
                    test_file=t_file,
                    skill_path=args.skill,
                    max_attempts=args.max_attempts,
                    report_dir=args.report_dir,
                )
                if not success:
                    all_success = False

        sys.exit(0 if all_success else 1)

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
