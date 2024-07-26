from typing import List, Tuple, Dict
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import tempfile
import subprocess
import os
from pydantic import BaseModel
from gitmuse.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


class StagedFile(BaseModel):
    status: str
    file_path: str


class IgnoredFile(BaseModel):
    file_path: str


def display_table(
    title: str, columns: List[Tuple[str, str]], rows: List[Tuple[str, str]]
) -> None:
    table = Table(
        title=title, title_justify="left", style="bold magenta"
    )  # Cambiado a "bold magenta"
    for col_name, col_style in columns:
        table.add_column(col_name, style=col_style)

    for row in rows:
        table.add_row(*row)

    console.print(table)
    logger.debug(f"Displayed table: {title}")


def display_changes(
    staged_files: List[Tuple[str, str]], ignored_files: List[IgnoredFile]
) -> None:
    changes: Dict[str, List[str]] = {"A": [], "M": [], "D": []}
    for status, file_path in staged_files:
        changes[status].append(file_path)

    rows: List[Tuple[str, str]] = []
    for status, files in changes.items():
        status_word = {"A": "New file", "M": "Modified", "D": "Deleted"}[status]
        for file_path in files:
            rows.append((status_word, file_path))

    display_table(
        "Changes to be committed", [("Status", "cyan"), ("File", "green")], rows
    )

    if ignored_files:
        ignored_count = len(ignored_files)
        console.print(
            f"\n[bold yellow]Ignored {ignored_count} file(s) based on .gitignore rules:[/bold yellow]"
        )
        for ignored_file in ignored_files[:5]:
            console.print(f"  - {ignored_file.file_path}")
        if ignored_count > 5:
            console.print(f"  ... and {ignored_count - 5} more")
        logger.info(f"Ignored {ignored_count} files based on .gitignore rules")


def display_diff(diff: str) -> None:
    view_option = Prompt.ask(
        "How would you like to view the diff?",
        choices=["full", "summary", "none"],
        default="none",
    )
    if view_option == "none":
        console.print("[bold blue]Diff view skipped.[/bold blue]")
        logger.info("Diff view skipped by user")
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
    logger.info(f"Displayed diff view: {view_option}")


def edit_commit_message(initial_message: str) -> str:
    try:
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            temp_file.write(initial_message)
            temp_file.flush()
            editor = os.getenv("EDITOR", "nano")
            subprocess.run([editor, temp_file.name], check=True)
            temp_file.seek(0)
            edited_message = temp_file.read()
        logger.info("Commit message edited by user")
        return edited_message.strip()
    except subprocess.CalledProcessError:
        logger.error("Failed to open editor for commit message editing")
        console.print(
            "[bold red]Error: Failed to open editor. Using original message.[/bold red]"
        )
        return initial_message
    finally:
        os.remove(temp_file.name)


def perform_commit(message: str) -> None:
    if not Confirm.ask(
        "[bold yellow]Are you sure you want to commit with this message?[/bold yellow]",
        default=True,  # Cambiado a True para que 'y' sea el valor por defecto
    ):
        console.print("[bold blue]Commit cancelled.[/bold blue]")
        logger.info("Commit cancelled by user")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Committing changes...", total=None)

        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                capture_output=True,
                text=True,
            )
            progress.update(task, completed=True)
            console.print(
                f"[bold green]Commit successfully created.[/bold green]\n{result.stdout}"
            )
            logger.info("Commit successfully created")
        except subprocess.CalledProcessError as e:
            progress.update(task, completed=True)
            error_message = f"Git commit failed: {e.stderr}"
            console.print(f"[bold red]Error: {error_message}[/bold red]")
            logger.error(error_message)


def display_ai_model_info(provider: str) -> None:
    model_info = {
        "ollama": "Using Llama 3.1 model via Ollama for commit message generation.",
        "openai": "Using OpenAI's GPT model for commit message generation.",
    }
    info_message = model_info.get(
        provider, f"Using {provider} for commit message generation."
    )
    console.print(f"[bold green]{info_message}[/bold green]")
    logger.info(f"AI model info: {info_message}")


if __name__ == "__main__":
    # Test functions
    staged_files = [
        StagedFile(status="M", file_path="file1.py"),
        StagedFile(status="A", file_path="file2.md"),
        StagedFile(status="D", file_path="file3.js"),
    ]
    ignored_files = [
        IgnoredFile(file_path="ignored1.txt"),
        IgnoredFile(file_path="ignored2.log"),
    ]
    display_changes(
        [(file.status, file.file_path) for file in staged_files], ignored_files
    )

    sample_diff = "diff --git a/file1.py b/file1.py\n--- a/file1.py\n+++ b/file1.py\n@@ -1,3 +1,4 @@\n print('hello')\n+print('world')\n"
    display_diff(sample_diff)

    display_ai_model_info("ollama")
