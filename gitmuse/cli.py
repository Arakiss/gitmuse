from gitmuse.core.git_utils import (
    check_dependency,
    check_staging_area,
    get_gitignore_patterns,
    get_staged_files,
)
from gitmuse.core.diff_analyzer import get_diff
from gitmuse.core.message_generator import generate_commit_message
from gitmuse.ai.gpt_integration import (
    generate_commit_message as ai_generate_commit_message,
)
from gitmuse.ui.console_ui import (
    display_changes,
    display_diff,
    edit_commit_message,
    perform_commit,
)
from rich.panel import Panel
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def main() -> None:
    try:
        check_dependency("sgpt")
        check_staging_area()

        ignore_patterns = get_gitignore_patterns()
        staged_files = get_staged_files()
        if not staged_files:
            console.print("[bold yellow]No changes to commit.[/bold yellow]")
            return

        diff, ignored_files = get_diff(staged_files, ignore_patterns)
        display_changes(staged_files, ignored_files)
        display_diff(diff)

        prompt = generate_commit_message(diff)
        commit_msg = ai_generate_commit_message(prompt)
        console.print(Panel(commit_msg, title="Generated commit message", expand=False))

        if (
            Prompt.ask(
                ":pencil2: Do you want to edit the commit message?",
                choices=["y", "n"],
                default="y",
            )
            == "y"
        ):
            commit_msg = edit_commit_message(commit_msg)

        console.print(Panel(commit_msg, title="Final commit message", expand=False))

        if (
            Prompt.ask(
                ":white_check_mark: Do you want to commit with this message?",
                choices=["y", "n"],
                default="y",
            )
            == "y"
        ):
            perform_commit(commit_msg)
            console.print(
                ":tada: [bold green]Commit successfully created.[/bold green]"
            )
        else:
            console.print(
                ":no_entry_sign: [bold yellow]Commit cancelled.[/bold yellow]"
            )
    except RuntimeError as e:
        console.print(f":x: [bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    main()
