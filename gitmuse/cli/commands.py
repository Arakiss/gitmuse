from typing import Set, List, Tuple
from rich.panel import Panel
from rich.console import Console
from rich.prompt import Prompt
from gitmuse.core.git_utils import (
    check_staging_area,
    get_gitignore_patterns,
    get_staged_files,
    get_diff,
    should_ignore,
    StagedFile,
)
from gitmuse.core.message_generator import generate_commit_message
from gitmuse.cli.ui import (
    display_changes,
    display_diff,
    edit_commit_message,
    perform_commit,
    display_ai_model_info,
    IgnoredFile,
)
from gitmuse.utils.logging import get_logger
from gitmuse.config.settings import CONFIG, ConfigError

logger = get_logger(__name__)
console = Console()


def get_commit_files(
    staged_files: List[StagedFile], ignore_patterns: Set[str]
) -> Tuple[List[StagedFile], List[IgnoredFile], str]:
    diff_content = ""
    ignored_files: List[IgnoredFile] = []
    files_to_commit: List[StagedFile] = []

    for file in staged_files:
        if should_ignore(file.file_path, ignore_patterns, staged_files):
            ignored_files.append(IgnoredFile(file_path=file.file_path))
        elif file.status != "D":  # Skip deleted files
            file_diff = get_diff(file.file_path)
            if file_diff:
                diff_content += (
                    f"File: {file.file_path}\nStatus: {file.status}\n{file_diff}\n\n"
                )
                files_to_commit.append(file)
        else:
            files_to_commit.append(file)

    return files_to_commit, ignored_files, diff_content


def commit_command(provider: str = "") -> None:
    try:
        if not check_staging_area():
            logger.warning("No changes in the staging area.")
            console.print(
                "[bold yellow]No changes in the staging area. Add changes with 'git add' before running this script.[/bold yellow]"
            )
            return

        ignore_patterns: Set[str] = get_gitignore_patterns()
        staged_files: List[StagedFile] = get_staged_files()

        if not staged_files:
            logger.warning("No changes to commit.")
            console.print("[bold yellow]No changes to commit.[/bold yellow]")
            return

        files_to_commit, ignored_files, diff_content = get_commit_files(
            staged_files, ignore_patterns
        )

        if not files_to_commit:
            logger.warning("No changes to commit after applying ignore patterns.")
            console.print(
                "[bold yellow]No changes to commit after applying ignore patterns.[/bold yellow]"
            )
            return

        files_to_commit_tuples: List[Tuple[str, str]] = [
            (file.status, file.file_path) for file in files_to_commit
        ]

        display_changes(files_to_commit_tuples, ignored_files)
        display_diff(diff_content)

        provider = provider or CONFIG.get_ai_provider() or "ollama"
        display_ai_model_info(provider)

        try:
            use_default_template = CONFIG.get_nested_config(
                "prompts", "commitMessage", "useDefault"
            )
            custom_template = CONFIG.get_nested_config(
                "prompts", "commitMessage", "customTemplate"
            )
        except ConfigError as e:
            logger.error(f"Error accessing commit message configuration: {str(e)}")
            use_default_template = True
            custom_template = ""

        commit_msg: str = generate_commit_message(
            diff_content,
            provider=provider,
            use_default_template=use_default_template,
            custom_template=custom_template,
        )

        logger.info("Generated commit message")
        console.print(Panel(commit_msg, title="Generated commit message", expand=False))

        if (
            Prompt.ask(
                ":pencil2: Do you want to edit the commit message?",
                choices=["y", "n"],
                default="n",
            )
            == "y"
        ):
            commit_msg = edit_commit_message(commit_msg)
            logger.info("Commit message edited by user")

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
            logger.info("Commit successfully created")
            console.print(
                ":tada: [bold green]Commit successfully created.[/bold green]"
            )
        else:
            logger.info("Commit cancelled by user")
            console.print(
                ":no_entry_sign: [bold yellow]Commit cancelled.[/bold yellow]"
            )

    except Exception as e:
        logger.exception(f"Error during commit process: {str(e)}")
        console.print(f":x: [bold red]Error during commit process:[/bold red] {str(e)}")


if __name__ == "__main__":
    commit_command()  # For testing purposes
