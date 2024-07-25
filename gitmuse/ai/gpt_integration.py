from gitmuse.core.git_utils import run_command
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

console = Console()


def generate_commit_message(prompt: str) -> str:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Generating commit message...", total=None)
        result = run_command(["sgpt", "--model", "gpt-4", "--code", prompt])
        progress.update(task, completed=True)

    if result.returncode != 0:
        raise RuntimeError(
            "Failed to generate commit message. Using a default message."
        )

    return result.stdout.strip()
