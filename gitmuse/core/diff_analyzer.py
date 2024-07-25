from typing import List, Tuple, Set, Dict
import difflib
from gitmuse.core.git_utils import run_command, should_ignore

ADDITIONAL_IGNORE_PATTERNS = {
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "bun.lock",
}


class GitDiffAnalyzer:
    def __init__(self, ignore_patterns: Set[str]):
        self.ignore_patterns = ignore_patterns.union(ADDITIONAL_IGNORE_PATTERNS)

    def get_diff(self, staged_files: List[Tuple[str, str]]) -> Tuple[str, List[str]]:
        filtered_diff = ""
        ignored_files = []

        for status, file_path in staged_files:
            if should_ignore(file_path, self.ignore_patterns):
                ignored_files.append(file_path)
                continue

            old_content, new_content = self._get_file_contents(status, file_path)
            diff = self._generate_diff(file_path, old_content, new_content)
            filtered_diff += f"File: {file_path}\nStatus: {status}\n{''.join(diff)}\n"

        return filtered_diff, ignored_files

    def _get_file_contents(self, status: str, file_path: str) -> Tuple[str, str]:
        if status == "A":
            return "", run_command(["git", "show", f":0:{file_path}"]).stdout
        elif status == "D":
            return run_command(["git", "show", f"HEAD:{file_path}"]).stdout, ""
        else:
            old_content = run_command(["git", "show", f"HEAD:{file_path}"]).stdout
            new_content = run_command(["git", "show", f":0:{file_path}"]).stdout
            return old_content, new_content

    def _generate_diff(
        self, file_path: str, old_content: str, new_content: str
    ) -> List[str]:
        return list(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
            )
        )

    def analyze_diff(self, diff: str) -> Dict[str, List[Dict[str, str]]]:
        changes = {"added": [], "modified": [], "deleted": []}
        current_file = ""
        current_status = ""
        current_content = []

        for line in diff.split("\n"):
            if line.startswith("File:"):
                if current_file:  # Save the changes of the previous file
                    changes[current_status].append(
                        {
                            "file": current_file,
                            "content": "".join(current_content).strip(),
                        }
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


def analyze_diff(diff: str) -> Dict[str, List[Dict[str, str]]]:
    analyzer = GitDiffAnalyzer(set())
    return analyzer.analyze_diff(diff)
