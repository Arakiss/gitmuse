import os
import subprocess
from typing import List, Optional, Set, Tuple
import fnmatch


def run_command(
    command: List[str], input_text: Optional[str] = None
) -> subprocess.CompletedProcess:
    return subprocess.run(command, input=input_text, capture_output=True, text=True)


def check_dependency(dependency: str) -> None:
    if run_command(["which", dependency]).returncode != 0:
        raise RuntimeError(
            f"{dependency} is not installed. Please install it with 'pip install {dependency}'."
        )


def check_staging_area() -> None:
    if run_command(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        raise RuntimeError(
            "No changes in the staging area. Add changes with 'git add' before running this script."
        )


def get_staged_files() -> List[Tuple[str, str]]:
    result = run_command(["git", "diff", "--cached", "--name-status"])
    return [tuple(line.split("\t")) for line in result.stdout.splitlines()]


def get_gitignore_patterns() -> Set[str]:
    ignore_patterns = set()
    for root, _, files in os.walk("."):
        if ".gitignore" in files:
            with open(os.path.join(root, ".gitignore"), "r") as f:
                ignore_patterns.update(
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                )
    return ignore_patterns


def should_ignore(file_path: str, ignore_patterns: Set[str]) -> bool:
    return any(
        fnmatch.fnmatch(file_path, pattern[1:])
        if pattern.startswith("/")
        else fnmatch.fnmatch(file_path, pattern)
        if "/" in pattern
        else fnmatch.fnmatch(os.path.basename(file_path), pattern)
        for pattern in ignore_patterns
    )
