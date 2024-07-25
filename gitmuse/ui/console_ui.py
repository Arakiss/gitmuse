from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.syntax import Syntax
from rich.panel import Panel
import tempfile
import subprocess
import os
from typing import List, Tuple

console = Console()


def display_changes(
    staged_files: List[Tuple[str, str]], ignored_files: List[str]
) -> None:
    console.print(
        f"\n[bold yellow]Ignored {len(ignored_files)} file(s) based on .gitignore rules.[/bold yellow]"
    )
    if ignored_files:
        console.print("Ignored files:")
        for file in ignored_files[:5]:
            console.print(f"  - {file}")
        if len(ignored_files) > 5:
            console.print(f"  ... and {len(ignored_files) - 5} more")

    console.print("\n[bold green]Changes to be committed:[/bold green]")
    for status, file_path in staged_files:
        status_word = {"A": "new file", "M": "modified", "D": "deleted"}.get(
            status, "unknown"
        )
        console.print(f"  {status_word}:   {file_path}")


def display_diff(diff: str) -> None:
    view_option = Prompt.ask(
        "How would you like to view the diff?",
        choices=["full", "summary", "none"],
        default="summary",
    )
    if view_option != "none":
        max_lines = (
            0
            if view_option == "full"
            else IntPrompt.ask(
                "How many lines of diff do you want to see? (0 for all)", default=10
            )
        )
        diff_preview = (
            diff if max_lines == 0 else "\n".join(diff.splitlines()[:max_lines])
        )
        console.print(
            Panel(
                Syntax(diff_preview, "diff", theme="monokai", line_numbers=True),
                title=f"{'Full' if max_lines == 0 else f'First {max_lines} lines of'} changes in staging area",
                expand=False,
            )
        )
    else:
        console.print("[bold blue]Diff view skipped.[/bold blue]")


def edit_commit_message(initial_message: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(initial_message)
        temp_file.flush()
        subprocess.run([os.getenv("EDITOR", "nano"), temp_file.name])
        temp_file.seek(0)
        edited_message = temp_file.read()
    os.remove(temp_file.name)
    return edited_message.strip()


def perform_commit(message: str) -> None:
    subprocess.run(["git", "commit", "-m", message])
