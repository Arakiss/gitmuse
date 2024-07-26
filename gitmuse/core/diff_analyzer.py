from typing import List, Tuple, Set, Dict, Literal, Sequence
import difflib
from gitmuse.core.git_utils import (
    get_gitignore_patterns,
    get_staged_files,
    run_command,
    should_ignore,
    StagedFile,
)
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel
import logging

ADDITIONAL_IGNORE_PATTERNS = {
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "bun.lock",
}

FileStatus = Literal["A", "M", "D"]

console = Console()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class GitDiffAnalyzer:
    def __init__(self, ignore_patterns: Set[str], staged_files: Sequence[StagedFile]):
        """
        Initializes the GitDiffAnalyzer.

        :param ignore_patterns: A set of file patterns to ignore.
        :param staged_files: A list of StagedFile instances containing the status and path of staged files.
        """
        self.ignore_patterns = ignore_patterns.union(ADDITIONAL_IGNORE_PATTERNS)
        self.staged_files = staged_files

    def get_diff(self, staged_files: Sequence[StagedFile]) -> Tuple[str, List[str]]:
        """
        Gets the diff for the staged files.

        :param staged_files: A list of StagedFile instances containing the status and path of staged files.
        :return: A tuple with the filtered diff and a list of ignored files.
        """
        filtered_diff = ""
        ignored_files = []

        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Processing staged files...", total=len(staged_files)
            )

            for file in staged_files:
                progress.update(task, advance=1)
                if should_ignore(file.file_path, self.ignore_patterns, staged_files):
                    ignored_files.append(file.file_path)
                    logging.info(f"Ignored file: {file.file_path}")
                    continue

                old_content, new_content = self._get_file_contents(
                    file.status, file.file_path
                )
                diff = self._generate_diff(file.file_path, old_content, new_content)
                emoji_status = self._get_status_emoji(file.status)
                filtered_diff += f"{emoji_status} File: {file.file_path}\nStatus: {file.status}\n{''.join(diff)}\n"

        return filtered_diff, ignored_files

    def _get_file_contents(self, status: str, file_path: str) -> Tuple[str, str]:
        """
        Gets the file contents based on the status.

        :param status: The status of the file (A, M, D).
        :param file_path: The path of the file.
        :return: A tuple with the old and new content of the file.
        """
        try:
            if status == "A":
                return "", self._run_git_command([":0", file_path])
            elif status == "D":
                return self._run_git_command(["HEAD", file_path]), ""
            else:
                old_content = self._run_git_command(["HEAD", file_path])
                new_content = self._run_git_command([":0", file_path])
                return old_content, new_content
        except Exception as e:
            console.print(
                f"[bold red]Error retrieving file contents for {file_path}: {e}[/bold red]"
            )
            return "", ""

    def _run_git_command(self, ref_file: List[str]) -> str:
        """
        Runs a git show command and returns the content.

        :param ref_file: Reference and file for the git show command.
        :return: The content of the file.
        """
        return run_command(["git", "show", f"{ref_file[0]}:{ref_file[1]}"]).stdout

    def _generate_diff(
        self, file_path: str, old_content: str, new_content: str
    ) -> List[str]:
        """
        Generates a unified diff between the old and new content of the file.

        :param file_path: The path of the file.
        :param old_content: The old content of the file.
        :param new_content: The new content of the file.
        :return: A list of lines representing the diff.
        """
        return list(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
            )
        )

    def analyze_diff(self, diff: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Analyzes the diff and categorizes the changes.

        :param diff: The diff as a string.
        :return: A dictionary with categorized changes.
        """
        changes: Dict[str, List[Dict[str, str]]] = {
            "added": [],
            "modified": [],
            "deleted": [],
        }
        current_file = ""
        current_status = ""
        current_content: List[str] = []

        for line in diff.split("\n"):
            if line.startswith("File:"):
                if current_file:  # Save the changes of the previous file
                    self._append_change(
                        changes, current_status, current_file, current_content
                    )
                current_file = line.split(": ", 1)[1].strip()
                current_content = []
            elif line.startswith("Status:"):
                current_status = {"A": "added", "M": "modified", "D": "deleted"}[
                    line.split(": ", 1)[1].strip()
                ]
            else:
                current_content.append(line + "\n")

        if current_file:  # Save the changes of the last file
            self._append_change(changes, current_status, current_file, current_content)

        return changes

    def _append_change(
        self,
        changes: Dict[str, List[Dict[str, str]]],
        status: str,
        file: str,
        content: List[str],
    ) -> None:
        """
        Appends a change to the changes dictionary.

        :param changes: The changes dictionary.
        :param status: The status of the change.
        :param file: The name of the file.
        :param content: The content of the change.
        """
        changes[status].append({"file": file, "content": "".join(content).strip()})

    def _get_status_emoji(self, status: str) -> str:
        """
        Gets the corresponding emoji for a file status.

        :param status: The status of the file.
        :return: A string containing the emoji.
        """
        return {"A": "➕", "M": "✏️", "D": "🗑️"}.get(status, "")


def analyze_diff(diff: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Helper function to analyze the diff.

    :param diff: The diff as a string.
    :return: A dictionary with categorized changes.
    """
    analyzer = GitDiffAnalyzer(set(), [])
    return analyzer.analyze_diff(diff)


def display_analysis(
    analysis: Dict[str, List[Dict[str, str]]], ignored_files: List[str]
) -> None:
    """
    Displays the analysis of the diff in a formatted table.

    :param analysis: The analysis dictionary.
    :param ignored_files: List of ignored files.
    """
    table = Table(title="Git Diff Analysis")
    table.add_column("Change Type", style="bold cyan")
    table.add_column("File", style="bold green")
    table.add_column("Content Preview", style="dim")

    for change_type, files in analysis.items():
        for file_info in files:
            content_preview = file_info["content"].split("\n")[0][:50]
            emoji = {"added": "➕", "modified": "✏️", "deleted": "🗑️"}.get(
                change_type, ""
            )
            table.add_row(
                f"{emoji} {change_type.capitalize()}",
                file_info["file"],
                content_preview + ("..." if len(content_preview) == 50 else ""),
            )

    console.print(Panel.fit(table, title="Analysis Summary"))

    if ignored_files:
        ignored_panel = Panel.fit(
            "\n".join(ignored_files), title="Ignored Files", style="bold yellow"
        )
        console.print(ignored_panel)


def main() -> None:
    ignore_patterns = get_gitignore_patterns()
    staged_files: List[StagedFile] = get_staged_files()
    if not staged_files:
        console.print("[bold yellow]No changes to commit.[/bold yellow]")
        return

    analyzer = GitDiffAnalyzer(ignore_patterns, staged_files)
    diff, ignored_files = analyzer.get_diff(staged_files)
    analysis = analyzer.analyze_diff(diff)
    display_analysis(analysis, ignored_files)


if __name__ == "__main__":
    main()
