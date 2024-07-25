from typing import List, Tuple, Set, Dict
from gitmuse.core.git_utils import run_command, should_ignore


def get_diff(
    staged_files: List[Tuple[str, str]], ignore_patterns: Set[str]
) -> Tuple[str, List[str]]:
    filtered_diff = ""
    ignored_files = []
    for status, file_path in staged_files:
        if should_ignore(file_path, ignore_patterns):
            ignored_files.append(file_path)
        if status == "A":
            file_diff = run_command(
                ["git", "diff", "--cached", "--", "/dev/null", file_path]
            ).stdout
        else:
            file_diff = run_command(["git", "diff", "--cached", "--", file_path]).stdout
        filtered_diff += f"File: {file_path}\nStatus: {status}\n{file_diff}\n\n"
    return filtered_diff, ignored_files


def analyze_diff(diff: str) -> Dict[str, List[Dict[str, str]]]:
    changes = {"added": [], "modified": [], "deleted": []}
    current_file = ""
    current_status = ""
    current_content = ""

    for line in diff.split("\n"):
        if line.startswith("File:"):
            if current_file:
                changes[current_status].append(
                    {"file": current_file, "content": current_content.strip()}
                )
            current_file = line.split(": ", 1)[1].strip()
            current_content = ""
        elif line.startswith("Status:"):
            current_status = {"A": "added", "M": "modified", "D": "deleted"}[
                line.split(": ", 1)[1].strip()
            ]
        else:
            current_content += line + "\n"

    if current_file:
        changes[current_status].append(
            {"file": current_file, "content": current_content.strip()}
        )

    return changes
