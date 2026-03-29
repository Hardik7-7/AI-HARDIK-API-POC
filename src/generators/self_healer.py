"""
Self Healer — Phase 3.

Runs the generated pytest tests, detects failures, and uses the LLM to
automatically fix the test code. Repeats up to SELF_HEAL_MAX_ATTEMPTS times.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.llm.client import call_llm
from src.llm.prompt_builder import SkillFile
from src.utils.file_io import extract_code_from_llm_response, read_text, write_text

console = Console()

DEFAULT_MAX_ATTEMPTS = 3


def run_and_heal(
    test_dir: str = "output/tests",
    test_file: str = "test_generated.py",
    skill_path: str = "skills/api_testing_skill.md",
    max_attempts: int | None = None,
    report_dir: str = "output/reports",
) -> bool:
    """Run pytest tests and auto-heal failures using the LLM.

    Args:
        test_dir: Directory containing the generated test files.
        test_file: Name of the primary test file to heal (relative to test_dir).
        skill_path: Path to the skill .md file.
        max_attempts: Maximum number of fix attempts (default from env var).
        report_dir: Directory to save HTML test reports.

    Returns:
        True if all tests pass, False if they still fail after all attempts.
    """
    if max_attempts is None:
        max_attempts = int(os.getenv("SELF_HEAL_MAX_ATTEMPTS", str(DEFAULT_MAX_ATTEMPTS)))

    console.rule("[bold red]Self-Healing Test Runner (Phase 3)[/bold red]")
    console.print(
        f"[dim]Test dir: {test_dir} | Max heal attempts: {max_attempts}[/dim]"
    )

    test_file_path = Path(test_dir) / test_file
    if not test_file_path.exists():
        raise FileNotFoundError(
            f"Test file not found: '{test_file_path}'. "
            "Run Phase 2 first: python generate_tests.py"
        )

    skill = SkillFile(skill_path)
    Path(report_dir).mkdir(parents=True, exist_ok=True)

    active_test_file = test_file_path

    for attempt in range(1, max_attempts + 2):  # +1 for the final run after last fix
        is_last_check = attempt == max_attempts + 1

        console.print()
        if is_last_check:
            console.print("[yellow]Final verification run...[/yellow]")
        else:
            console.print(
                f"[bold]Run {attempt} of {max_attempts}[/bold] "
                f"{'(initial)' if attempt == 1 else f'(after fix #{attempt - 1})'}"
            )

        # ── Run pytest ─────────────────────────────────────────────────────────
        passed, failure_output, report_path = _run_pytest(str(active_test_file), report_dir, attempt)

        if passed:
            console.print()
            console.print(
                Panel(
                    "[green bold]✓ All tests passed![/green bold]\n\n"
                    + (
                        f"[dim]Fixed after {attempt - 1} heal attempt(s)[/dim]"
                        if attempt > 1
                        else "[dim]Tests passed on first run — no healing needed[/dim]"
                    )
                    + (f"\n[dim]Report: {report_path}[/dim]" if report_path else ""),
                    title="Phase 3 Complete",
                    border_style="green",
                )
            )
            
            # ── Cleanup ────────────────────────────────────────────────────────
            if active_test_file != test_file_path:
                # The tests passed on a generated fix file.
                # Remove the original failing file and rename the fix to the original filename.
                if test_file_path.exists():
                    test_file_path.unlink()
                active_test_file.rename(test_file_path)
                
                # Delete any other attempt files lingering around to clean up.
                stem = test_file_path.stem
                for p in Path(test_dir).glob(f"{stem}_attempt_*.py"):
                    if p.exists() and p != test_file_path:
                        p.unlink()

            return True

        if is_last_check:
            break

        # ── Tests failed — call LLM to fix ─────────────────────────────────────
        console.print(f"[red]Tests failed. Attempting auto-heal #{attempt}...[/red]")
        console.print(Panel(failure_output[:3000], title="Failure Output", border_style="red"))

        test_code = read_text(str(active_test_file))
        try:
            fixed_code = _heal_tests(skill, test_code, failure_output)

            # Show the LLM fix to the user
            console.print()
            console.print(
                Panel(
                    fixed_code[:4000]
                    + ("\n\n[dim]... (truncated, full code written to file)[/dim]" if len(fixed_code) > 4000 else ""),
                    title=f"[cyan]LLM Fix #{attempt} — Fixed Test Code[/cyan]",
                    border_style="cyan",
                )
            )

            # Instead of modifying the original, we create a new attempt file.
            next_active_file = test_file_path.parent / f"{test_file_path.stem}_attempt_{attempt}.py"
            write_text(str(next_active_file), fixed_code)
            console.print(f"[green]✓ Saved fix #{attempt} to {next_active_file}[/green]")
            
            # The next loop iteration will run pytest on this new file.
            active_test_file = next_active_file

        except RuntimeError as e:
            err_msg = str(e).lower()
            if "not valid python" in err_msg or "empty response" in err_msg:
                console.print(f"\n[bold yellow]Heal attempt generated invalid/empty code. Triggering full test regeneration from scenario...[/bold yellow]")
                
                stem = test_file_path.stem
                scenario_stem = stem[5:] if stem.startswith("test_") else stem
                scenario_path = Path("output/scenarios") / f"{scenario_stem}.json"
                
                if scenario_path.exists():
                    try:
                        from src.generators.code_generator import generate_tests
                        generate_tests(
                            test_cases_path=str(scenario_path),
                            skill_path=skill_path,
                            output_dir=test_dir,
                        )
                        # Revert back to the original test script which was just regenerated
                        active_test_file = test_file_path
                    except Exception as gen_e:
                        console.print(f"[red]Full generation also failed: {gen_e}[/red]")
                else:
                    console.print(f"[red]Cannot regenerate: Scenario file {scenario_path} not found.[/red]")
            else:
                raise

    # All attempts exhausted
    console.print()
    console.print(
        Panel(
            f"[red bold]✗ Tests still failing after {max_attempts} heal attempt(s)[/red bold]\n\n"
            "[dim]Review the failure output above and edit the test file manually.\n"
            f"Backups of each attempt are in: {test_dir}[/dim]",
            title="Phase 3 — Max Attempts Reached",
            border_style="red",
        )
    )
    return False


def _run_pytest(test_file_path: str, report_dir: str, attempt: int) -> tuple[bool, str, str]:
    """Run pytest and return (passed, failure_output, report_path)."""
    report_path = str(Path(report_dir) / f"report_attempt_{attempt}.html")

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_file_path,
        "-v",
        "--tb=short",
        f"--html={report_path}",
        "--self-contained-html",
        "--no-header",
    ]
    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("Running tests...", total=None)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )

    output = result.stdout + result.stderr
    passed = result.returncode == 0

    if passed:
        console.print("[green]✓ pytest exited with code 0 (all passed)[/green]")
    else:
        console.print(
            f"[red]✗ pytest exited with code {result.returncode}[/red]"
        )

    return passed, output, report_path


def _heal_tests(
    skill: SkillFile,
    test_code: str,
    failure_output: str,
) -> str:
    """Use the LLM to fix failing test code.

    Returns:
        The complete fixed test file as a string.
    """
    console.print("[yellow]Calling LLM to analyze failures and generate fix...[/yellow]")
    prompt = skill.build_prompt(
        "self_heal",
        TEST_CODE=test_code,
        FAILURE_OUTPUT=failure_output,
    )
    raw_response = call_llm(prompt)
    fixed_code = extract_code_from_llm_response(raw_response)

    if not fixed_code.strip():
        raise RuntimeError(
            "LLM returned an empty response for self-heal. "
            "The test file was NOT overwritten. "
            "Check the LLM output above for finish_reason details."
        )

    try:
        ast.parse(fixed_code)
    except SyntaxError as e:
        raise RuntimeError(
            f"Healed code is not valid Python (likely truncated by LLM): {e}\n"
            "The test file was NOT overwritten. "
            "Re-running will trigger a fresh retry."
        ) from e

    return fixed_code

