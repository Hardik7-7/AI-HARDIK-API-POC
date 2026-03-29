"""
End-to-End Test Automation (Phase 2 & Phase 3)

Usage:
  python generate_run_heal.py

This script automatically executes Phase 2 (Bulk code generation for all scenarios)
and immediately follows it up with Phase 3 (Bulk run & healing for all generated tests).
"""
import subprocess
import sys
from rich.console import Console

console = Console()

def main():
    console.rule("[bold cyan]Starting Automated Test Generation & Healing Pipeline[/bold cyan]")
    
    # Run Phase 2
    console.print("\n[bold blue]>>> Executing Phase 2: generate_tests.py[/bold blue]")
    result_phase2 = subprocess.run([sys.executable, "generate_tests.py"])
    
    if result_phase2.returncode != 0:
        console.print("[bold red]Phase 2 failed. Aborting pipeline.[/bold red]")
        sys.exit(result_phase2.returncode)
        
    # Run Phase 3
    console.print("\n[bold blue]>>> Executing Phase 3: run_and_heal.py[/bold blue]")
    result_phase3 = subprocess.run([sys.executable, "run_and_heal.py"])
    
    if result_phase3.returncode != 0:
        console.print("\n[bold red]Pipeline complete but some tests failed to heal.[/bold red]")
        sys.exit(result_phase3.returncode)
    else:
        console.print("\n[bold green]✓ Pipeline complete! All tests automatically generated and healed.[/bold green]")
        sys.exit(0)

if __name__ == "__main__":
    main()
