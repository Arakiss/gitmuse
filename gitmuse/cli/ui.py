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
from gitmuse.utils.logging import get_logger
from gitmuse.config.settings import CONFIG, ConfigError
from gitmuse.models import StagedFile, IgnoredFile

logger = get_logger(__name__)
console = Console()


def display_table(
    title: str, columns: List[Tuple[str, str]], rows: List[List[str]]
) -> None:
    """
    Display a table with a given title, columns, and rows.
    """
    table = Table(title=title, title_justify="left", style="bold magenta")
    for col_name, col_style in columns:
        table.add_column(col_name, style=col_style)

    for row in rows:
        table.add_row(*row)

    console.print(table)
    logger.debug(f"Displayed table: {title}")


def display_changes(
    changes: List[StagedFile], ignored_files: List[IgnoredFile]
) -> None:
    changes_dict: Dict[str, List[str]] = {
        "Added": [],
        "Modified": [],
        "Deleted": [],
        "Renamed": [],
        "Ignored": [file.file_path for file in ignored_files],
    }

    for file in changes:
        if file.status.startswith('A'):
            changes_dict["Added"].append(file.file_path)
        elif file.status.startswith('M'):
            changes_dict["Modified"].append(file.file_path)
        elif file.status.startswith('D'):
            changes_dict["Deleted"].append(file.file_path)
        elif file.status.startswith('R'):
            changes_dict["Renamed"].append(file.file_path)

    table = Table(title="Changes", title_justify="left", style="bold magenta")
    table.add_column("Status", style="cyan")
    table.add_column("Files", style="green")

    for status, files in changes_dict.items():
        if files:
            table.add_row(status, "\n".join(files))

    console.print(table)
    logger.debug("Displayed changes table")


def display_diff(diff: str) -> None:
    """
    Ask the user how they would like to view the diff and display it accordingly.
    """

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
    """
    Open the default editor to allow the user to edit the commit message.
    The editor to use can be set via the EDITOR environment variable.
    """
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
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to open editor: {e}")
        console.print("[bold red]Error: Failed to open editor. Using original message.[/bold red]")
        return initial_message
    finally:
        os.remove(temp_file.name)


def perform_commit(message: str) -> None:
    """
    Ask the user to confirm the commit message and perform the commit if confirmed.
    """
    if not Confirm.ask(
        "[bold yellow]Are you sure you want to commit with this message?[/bold yellow]",
        default=True,
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
    """
    Display information about the AI model based on the provider.
    """
    try:
        model = CONFIG.get_ai_model()
    except ConfigError:
        logger.warning("Failed to get AI model from config. Using default.")
        model = "default model"

    model_info = {
        "ollama": f"Using {model} model via Ollama for commit message generation.",
        "openai": f"Using OpenAI's {model} model for commit message generation.",
    }
    info_message = model_info.get(
        provider, f"Using {provider} ({model}) for commit message generation."
    )
    console.print(f"[bold green]{info_message}[/bold green]")
    logger.info(f"AI model info: {info_message}")


def display_commit_message(message: str, title: str) -> None:
    """
    Display the commit message in a panel that wraps text properly.
    """
    wrapped_message = "\n".join(
        line.strip() for line in message.split("\n") if line.strip()
    )
    panel = Panel(
        wrapped_message,
        title=title,
        expand=False,
        border_style="green",
        padding=(1, 1),
    )
    console.print(panel)


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
    display_changes(staged_files, ignored_files)

    sample_diff = "diff --git a/file1.py b/file1.py\n--- a/file1.py\n+++ b/file1.py\n@@ -1,3 +1,4 @@\n print('hello')\n+print('world')\n"
    display_diff(sample_diff)

    display_ai_model_info("ollama")