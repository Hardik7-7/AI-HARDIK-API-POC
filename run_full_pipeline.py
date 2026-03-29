"""
End-to-End Test Automation Pipeline (Phases 1, 2, 3 + Sheets Integration)

Usage Example:
  python run_full_pipeline.py --swagger inputs/swagger/api-doc.md --story inputs/stories/create_library.md

This script executes the entire lifecycle:
1. Scenario Generation (extracts scenarios from story)
2. Google Sheets Review (pushes to sheets for external review)
3. Test Code Generation (turns reviewed scenarios into python code)
4. Self-Healing Test Runner (runs tests and auto-fixes them)
"""
import argparse
import os
import subprocess
import sys
from rich.console import Console

console = Console()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Full Pipeline: Generate Scenarios -> Sheets Sync -> Generate Tests -> Run & Heal",
    )
    parser.add_argument("--swagger", "-s", required=True, help="Path to Swagger/OpenAPI file")
    parser.add_argument("--stories", "-t", required=True, nargs="+", help="Path(s) to user story file(s)")
    parser.add_argument("--skill", default="skills/api_testing_skill.md", help="Path to skill file")
    return parser.parse_args()

def main():
    args = parse_args()
    console.rule("[bold cyan]Starting Full End-to-End AI Pipeline[/bold cyan]")

    # ── Step 1: Scenario Generation ─────────────────────────────────────────
    console.print("\n[bold blue]>>> [Step 1] Executing Phase 1: generate_scenarios.py[/bold blue]")
    cmd1 = [
        sys.executable, "generate_scenarios.py",
        "--swagger", args.swagger,
        "--skill", args.skill,
        "--stories"
    ] + args.stories
    res1 = subprocess.run(cmd1)
    if res1.returncode != 0:
        console.print("[bold red]Phase 1 failed. Aborting pipeline.[/bold red]")
        sys.exit(res1.returncode)

    # ── Step 2: Google Sheets Review Pipeline ───────────────────────────────
    console.print("\n[bold blue]>>> [Step 2] Launching Google Sheets Review Pipeline...[/bold blue]")
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(CURRENT_DIR)

    sheets_dir = os.path.join(ROOT_DIR, "AI-QA-Sheets-Integration")

    # Intelligently adapt venv path for Windows vs Linux depending on where it's run
    if os.name == 'nt':
        venv_python = os.path.join(sheets_dir, ".venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(sheets_dir, ".venv", "bin", "python3")

    script_path = os.path.join(sheets_dir, "main.py")
    scenarios_json = os.path.join(CURRENT_DIR, "output", "scenarios", "all_scenarios.json")

    if os.path.exists(script_path):
        try:
            cmd_sheets = ["--input", scenarios_json]
            if os.path.exists(venv_python):
                subprocess.run([venv_python, script_path] + cmd_sheets, cwd=sheets_dir, check=True)
            else:
                subprocess.run([sys.executable, script_path] + cmd_sheets, cwd=sheets_dir, check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Sheets sync failed with exit code {e.returncode}. Aborting pipeline.[/bold red]")
            sys.exit(e.returncode)
    else:
        console.print(f"[bold yellow][WARNING] Sheets script not found at: {script_path}[/bold yellow]")

    # ── Step 3: Test Generation & Healing ───────────────────────────────────
    console.print("\n[bold blue]>>> [Step 3] Executing Phase 2 & 3: generate_run_heal.py[/bold blue]")
    cmd23 = [sys.executable, "generate_run_heal.py"]
    res23 = subprocess.run(cmd23)
    if res23.returncode != 0:
        console.print("\n[bold red]Pipeline complete but some tests failed to heal.[/bold red]")
        sys.exit(res23.returncode)

    console.print("\n[bold green]✓ Full Pipeline complete successfully![/bold green]")
    sys.exit(0)

if __name__ == "__main__":
    main()