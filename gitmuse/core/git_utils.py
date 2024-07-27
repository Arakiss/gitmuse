import os
import subprocess
from typing import List, Optional, Set, Sequence, Literal, Tuple
import fnmatch
from rich.console import Console
from functools import lru_cache
from pydantic import BaseModel, validator

console = Console()


class StagedFile(BaseModel):
    status: Literal["A", "M", "D", "R100"]
    file_path: str

    @validator("status")
    def validate_status(cls, v):
        allowed_statuses = ["A", "M", "D", "R100"]
        if v not in allowed_statuses:
            raise ValueError("Input should be 'A', 'M', 'D' or 'R100'")
        return v


def run_command(
    command: List[str], input_text: Optional[str] = None, check: bool = False
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            command, input=input_text, capture_output=True, text=True, check=check
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[bold yellow]Command failed:[/bold yellow] {' '.join(command)}")
        console.print(f"[bold yellow]Error message:[/bold yellow] {e.stderr}")
        raise


def check_dependency(dependency: str) -> None:
    result = run_command(["which", dependency])
    if result.returncode != 0:
        raise RuntimeError(
            f"{dependency} is not installed. Please install it with 'pip install {dependency}'."
        )


def check_staging_area() -> bool:
    result = run_command(["git", "diff", "--cached", "--quiet"])
    return result.returncode != 0


@lru_cache(maxsize=1)
def get_staged_files() -> List[StagedFile]:
    result = run_command(["git", "diff", "--cached", "--name-status"])
    staged_files: List[StagedFile] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            staged_files.append(StagedFile(status=parts[0], file_path=parts[1]))
        else:
            console.print(
                f"[bold yellow]Warning: Unexpected git diff output: {line}[/bold yellow]"
            )
    console.print(f"Staged files: {staged_files}")
    return staged_files


@lru_cache(maxsize=1)
def get_gitignore_patterns() -> Set[str]:
    ignore_patterns: Set[str] = set()
    for root, _, files in os.walk("."):
        if ".gitignore" in files:
            with open(os.path.join(root, ".gitignore"), "r") as f:
                ignore_patterns.update(
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                )
    console.print(f"Loaded gitignore patterns: {ignore_patterns}")
    return ignore_patterns


def should_ignore(
    file_path: str, ignore_patterns: Set[str], staged_files: Sequence[StagedFile]
) -> bool:
    if file_path in [file.file_path for file in staged_files]:
        return False
    for pattern in ignore_patterns:
        if (
            (pattern.startswith("/") and fnmatch.fnmatch(file_path, pattern[1:]))
            or (fnmatch.fnmatch(file_path, pattern))
            or ("/" in pattern and fnmatch.fnmatch(file_path, pattern))
            or (fnmatch.fnmatch(os.path.basename(file_path), pattern))
        ):
            console.print(f"File {file_path} ignored due to pattern: {pattern}")
            return True
    return False


def get_file_content(file_path: str, revision: str = "HEAD") -> str:
    try:
        if revision == "staged":
            result = run_command(["git", "show", f":0:{file_path}"])
        else:
            result = run_command(["git", "show", f"{revision}:{file_path}"])

        if result.returncode == 0:
            return result.stdout
        else:
            console.print(
                f"[bold yellow]Warning: Could not get content for {file_path} at {revision}[/bold yellow]"
            )
            return ""
    except Exception as e:
        console.print(
            f"[bold yellow]Error getting file content: {str(e)}[/bold yellow]"
        )
        return ""


def get_diff(file_path: str) -> str:
    try:
        if os.path.exists(file_path):
            result = run_command(["git", "diff", "--cached", file_path])
        else:
            result = run_command(
                ["git", "diff", "--cached", "--", "/dev/null", file_path]
            )

        if result.returncode == 0:
            return result.stdout
        else:
            console.print(
                f"[bold yellow]Warning: Could not get diff for {file_path}[/bold yellow]"
            )
            return ""
    except Exception as e:
        console.print(f"[bold yellow]Error getting diff: {str(e)}[/bold yellow]")
        return ""


def get_full_diff() -> str:
    result = run_command(["git", "diff", "--cached"])
    if result.returncode == 0:
        return result.stdout
    else:
        console.print("[bold yellow]Warning: Could not get full diff[/bold yellow]")
        return ""


def get_repo_root() -> str:
    result = run_command(["git", "rev-parse", "--show-toplevel"])
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        raise RuntimeError("Not in a git repository")


def get_commit_files() -> Tuple[List[StagedFile], str]:
    staged_files = get_staged_files()
    full_diff = get_full_diff()
    return staged_files, full_diff


if __name__ == "__main__":
    # Test functions
    print("Checking staging area...")
    print(f"Changes in staging area: {check_staging_area()}")

    print("\nGetting staged files...")
    staged_files = get_staged_files()
    for file in staged_files:
        print(f"{file.status}: {file.file_path}")

    print("\nGetting .gitignore patterns...")
    ignore_patterns = get_gitignore_patterns()
    print(f"Ignore patterns: {ignore_patterns}")

    print("\nGetting full diff...")
    full_diff = get_full_diff()
    print(f"Full diff preview: {full_diff[:200]}...")

    if staged_files:
        test_file = staged_files[0].file_path
        print(f"\nGetting content for {test_file}...")
        content = get_file_content(test_file, "staged")
        print(f"Content preview: {content[:100]}...")

        print(f"\nGetting diff for {test_file}...")
        diff = get_diff(test_file)
        print(f"Diff preview: {diff[:100]}...")

    print("\nGetting repository root...")
    print(f"Repo root: {get_repo_root()}")

    print("\nGetting commit files...")
    commit_files, commit_diff = get_commit_files()
    print(f"Number of staged files: {len(commit_files)}")
    print(f"Full diff length: {len(commit_diff)} characters")
