from typing import List, Tuple
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
import tempfile
import subprocess
import os

console = Console()


def display_changes(
    staged_files: List[Tuple[str, str]], ignored_files: List[str]
) -> None:
    changes = {"A": [], "M": [], "D": []}
    for status, file_path in staged_files:
        changes[status].append(file_path)

    table = Table(title="Changes to be committed", title_justify="full")
    table.add_column("Status", style="cyan")
    table.add_column("File", style="green")

    for status, files in changes.items():
        status_word = {"A": "New file", "M": "Modified", "D": "Deleted"}[status]
        for file in files:
            table.add_row(status_word, file)

    console.print(table)

    if ignored_files:
        console.print(
            f"\n[bold yellow]Ignored {len(ignored_files)} file(s) based on .gitignore rules:[/bold yellow]"
        )
        for file in ignored_files[:5]:
            console.print(f"  - {file}")
        if len(ignored_files) > 5:
            console.print(f"  ... and {len(ignored_files) - 5} more")


def display_diff(diff: str) -> None:
    view_option = Prompt.ask(
        "How would you like to view the diff?",
        choices=["full", "summary", "none"],
        default="none",
    )
    if view_option == "none":
        console.print("[bold blue]Diff view skipped.[/bold blue]")
        return

    max_lines = (
        0
        if view_option == "full"
        else IntPrompt.ask(
            "How many lines of diff do you want to see? (0 for all)", default=10
        )
    )
    diff_preview = diff if max_lines == 0 else "\n".join(diff.splitlines()[:max_lines])
    title = (
        "Full changes in staging area"
        if max_lines == 0
        else f"First {max_lines} lines of changes in staging area"
    )

    console.print(
        Panel(
            Syntax(diff_preview, "diff", theme="monokai", line_numbers=True),
            title=title,
            expand=False,
        )
    )


def edit_commit_message(initial_message: str) -> str:
    try:
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            temp_file.write(initial_message)
            temp_file.flush()
            editor = os.getenv("EDITOR", "nano")
            subprocess.run([editor, temp_file.name], check=True)
            temp_file.seek(0)
            edited_message = temp_file.read()
        return edited_message.strip()
    except subprocess.CalledProcessError:
        console.print(
            "[bold red]Error: Failed to open editor. Using original message.[/bold red]"
        )
        return initial_message
    finally:
        os.remove(temp_file.name)


def perform_commit(message: str) -> None:
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message], check=True, capture_output=True, text=True
        )
        console.print(result.stdout)
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error: Git commit failed.[/bold red]\n{e.stderr}")


def display_ai_model_info(provider: str) -> None:
    if provider == "ollama":
        console.print(
            "[bold green]Using Llama 3.1 model via Ollama for commit message generation.[/bold green]"
        )
    elif provider == "openai":
        console.print(
            "[bold green]Using OpenAI's GPT model for commit message generation.[/bold green]"
        )
    else:
        console.print(
            f"[bold yellow]Using {provider} for commit message generation.[/bold yellow]"
        )


if __name__ == "__main__":
    # Test functions
    staged_files = [("M", "file1.py"), ("A", "file2.md"), ("D", "file3.js")]
    ignored_files = ["ignored1.txt", "ignored2.log"]
    display_changes(staged_files, ignored_files)

    sample_diff = "diff --git a/file1.py b/file1.py\n--- a/file1.py\n+++ b/file1.py\n@@ -1,3 +1,4 @@\n print('hello')\n+print('world')\n"
    display_diff(sample_diff)

    display_ai_model_info("ollama")
