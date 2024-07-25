from typing import List, Tuple, Set, Dict
import difflib
from gitmuse.core.git_utils import (
    get_gitignore_patterns,
    get_staged_files,
    run_command,
    should_ignore,
)
from rich.console import Console
from rich.table import Table

ADDITIONAL_IGNORE_PATTERNS = {
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "bun.lock",
}

console = Console()


def get_diff(
    staged_files: List[Tuple[str, str]], ignore_patterns: Set[str]
) -> Tuple[str, List[str]]:
    filtered_diff = ""
    ignored_files = []
    combined_ignore_patterns = ignore_patterns.union(ADDITIONAL_IGNORE_PATTERNS)

    for status, file_path in staged_files:
        if should_ignore(file_path, combined_ignore_patterns):
            ignored_files.append(file_path)
            continue

        if status == "A":
            old_content = ""
            new_content = run_command(["git", "show", f":0:{file_path}"]).stdout
        elif status == "D":
            old_content = run_command(["git", "show", f"HEAD:{file_path}"]).stdout
            new_content = ""
        else:
            old_content = run_command(["git", "show", f"HEAD:{file_path}"]).stdout
            new_content = run_command(["git", "show", f":0:{file_path}"]).stdout

        diff = list(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
            )
        )

        filtered_diff += f"File: {file_path}\nStatus: {status}\n{''.join(diff)}\n"

    return filtered_diff, ignored_files


def analyze_diff(diff: str) -> Dict[str, List[Dict[str, str]]]:
    changes = {"added": [], "modified": [], "deleted": []}
    current_file = ""
    current_status = ""
    current_content = []

    for line in diff.split("\n"):
        if line.startswith("File:"):
            if current_file:  # Save the changes of the previous file
                changes[current_status].append(
                    {"file": current_file, "content": "".join(current_content).strip()}
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
        changes[current_status].append(
            {"file": current_file, "content": "".join(current_content).strip()}
        )

    return changes


def display_analysis(
    analysis: Dict[str, List[Dict[str, str]]], ignored_files: List[str]
) -> None:
    table = Table(title="Git Diff Analysis")
    table.add_column("Change Type", style="bold cyan")
    table.add_column("File", style="bold green")
    table.add_column("Content Preview", style="dim")

    for change_type, files in analysis.items():
        for file_info in files:
            content_preview = file_info["content"].split("\n")[0][:50]
            table.add_row(
                change_type.capitalize(),
                file_info["file"],
                content_preview + ("..." if len(content_preview) == 50 else ""),
            )

    console.print(table)

    if ignored_files:
        console.print("\n[bold yellow]Ignored files:[/bold yellow]")
        for ignored_file in ignored_files:
            console.print(f"  - {ignored_file}")


def main() -> None:
    ignore_patterns = get_gitignore_patterns()
    staged_files = get_staged_files()
    if not staged_files:
        console.print("[bold yellow]No changes to commit.[/bold yellow]")
        return

    diff, ignored_files = get_diff(staged_files, ignore_patterns)
    analysis = analyze_diff(diff)
    display_analysis(analysis, ignored_files)


if __name__ == "__main__":
    main()
