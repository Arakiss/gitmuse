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

)
from gitmuse.cli.ui import (
    display_changes,
    display_diff,
    edit_commit_message,
    perform_commit,
    display_ai_model_info,
)
from gitmuse.models import StagedFile, IgnoredFile
from gitmuse.utils.logging import get_logger
from gitmuse.config.settings import CONFIG, ConfigError
from gitmuse.core.message_generator import generate_commit_message

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
        elif file.status[0] != "D":
            file_diff = get_diff(file.file_path)
            if file_diff:
                diff_content += (
                    f"File: {file.file_path}\nStatus: {file.status}\n{file_diff}\n\n"
                )
                files_to_commit.append(file)
        else:
            files_to_commit.append(file)

    return files_to_commit, ignored_files, diff_content


def get_commit_message_config() -> Tuple[bool, str]:
    try:
        use_default_template = CONFIG.get_nested_config(
            "prompts", "commitMessage", "useDefault"
        )
        custom_template = CONFIG.get_nested_config(
            "prompts", "commitMessage", "customTemplate"
        )
        return use_default_template, custom_template
    except ConfigError as e:
        console.print(f":warning: [bold yellow]Warning:[/bold yellow] {str(e)}")
        console.print(
            "[bold yellow]Using default commit message template due to configuration error.[/bold yellow]"
        )
        return True, ""


def commit_command(provider: str = "") -> None:
    try:
        # Check for changes in the staging area
        if not check_staging_area():
            logger.warning("No changes in the staging area.")
            console.print(
                "[bold yellow]No changes in the staging area. Add changes with 'git add' before running this script.[/bold yellow]"
            )
            return

        # Get the staged files and ignore patterns
        ignore_patterns: Set[str] = get_gitignore_patterns()
        staged_files: List[StagedFile] = get_staged_files()

        if not staged_files:
            logger.warning("No changes to commit.")
            console.print("[bold yellow]No changes to commit.[/bold yellow]")
            return

        # Display changes and diff to the user
        files_to_commit, ignored_files, diff_content = get_commit_files(
            staged_files, ignore_patterns
        )
        display_changes(files_to_commit, ignored_files)
        display_diff(diff_content)

        # Validate the provider and display AI model info
        provider = provider or CONFIG.get_ai_provider() or "ollama"
        if provider not in ["openai", "ollama"]:
            console.print(f":x: [bold red]Error:[/bold red] Unsupported AI provider: {provider}")
            return
        display_ai_model_info(provider)

        # Get commit message configuration
        use_default_template, custom_template = get_commit_message_config()

        # Generate commit message
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