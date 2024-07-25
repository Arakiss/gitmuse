import os
from typing import Dict, List, Tuple
from gitmuse.core.diff_analyzer import analyze_diff
from gitmuse.config.settings import COMMIT_KEYWORDS, DEFAULT_PROVIDER
from gitmuse.providers.openai import OpenAIProvider
from gitmuse.providers.ollama import OllamaProvider
from rich.console import Console

console = Console()


def get_provider(provider: str = DEFAULT_PROVIDER):
    providers = {"openai": OpenAIProvider, "ollama": OllamaProvider}
    provider_class = providers.get(provider)
    if provider_class is None:
        raise ValueError(f"Unsupported provider specified: {provider}")
    return provider_class()


def generate_commit_message(diff: str, provider: str = DEFAULT_PROVIDER) -> str:
    try:
        changes = analyze_diff(diff)
        files_summary, changes_summary = summarize_changes(changes)
        detailed_changes = generate_detailed_changes(changes)
        prompt_content = create_prompt_content(
            files_summary, changes_summary, detailed_changes
        )
        provider_instance = get_provider(provider)
        return provider_instance.generate_commit_message(prompt_content)
    except Exception as e:
        console.print(f"[bold red]Error generating commit message: {str(e)}[/bold red]")
        return (
            "📝 Update files\n\nAn error occurred while generating the commit message."
        )


def summarize_changes(changes: Dict[str, List[Dict[str, str]]]) -> Tuple[str, str]:
    files_changed = list(
        set(change["file"] for category in changes.values() for change in category)
    )
    files_summary = ", ".join(files_changed[:3]) + (
        "..." if len(files_changed) > 3 else ""
    )
    changes_summary = ", ".join(
        f"{category.capitalize()}: {len(items)} file(s)"
        for category, items in changes.items()
        if items
    )
    return files_summary, changes_summary


def generate_detailed_changes(changes: Dict[str, List[Dict[str, str]]]) -> List[str]:
    detailed_changes = []
    for category, items in changes.items():
        for item in items:
            file_ext = os.path.splitext(item["file"])[1]
            if file_ext == ".md":
                detailed_changes.append(
                    f"{category.capitalize()} documentation: {item['file']}"
                )
            elif file_ext in [".py", ".js", ".ts"]:
                detailed_changes.append(
                    f"{category.capitalize()} code in {item['file']}"
                )
            else:
                detailed_changes.append(f"{category.capitalize()} {item['file']}")
    return detailed_changes


def create_prompt_content(
    files_summary: str, changes_summary: str, detailed_changes: List[str]
) -> str:
    keywords = ", ".join([f"{emoji} {verb}" for verb, emoji in COMMIT_KEYWORDS.items()])
    return f"""
    Generate a git commit message for the following changes:
    Files changed: {files_summary}
    Summary: {changes_summary}

    Detailed changes:
    {' '.join(detailed_changes)}

    Follow these guidelines:
    1. Start with an emoji and an imperative present active verb from this list: {keywords}
    2. The first line should be a summary, maximum 50 characters (including the emoji)
    3. Leave a blank line after the summary
    4. Provide a more detailed description of the changes, focusing on the most significant modifications
    5. Use bullet points for multiple changes
    6. Be specific about what changed and why, mentioning key files or components that were affected
    7. Don't include the full file names in the message body

    Format the message like this:
    🎨 Verb Summary of changes

    - Detailed explanation of changes
    - Another point if necessary

    IMPORTANT: Provide ONLY the commit message, no additional explanations.
    """


if __name__ == "__main__":
    sample_diff = """
    diff --git a/gitmuse/core/diff_analyzer.py b/gitmuse/core/diff_analyzer.py
    index 2943b3d..b8d6785 100644
    --- a/gitmuse/core/diff_analyzer.py
    +++ b/gitmuse/core/diff_analyzer.py
    @@ -1,6 +1,7 @@
    import os
    from gitmuse.core.git_utils import get_git_diff, get_git_files
    +from gitmuse.config.settings import ADDITIONAL_IGNORE_PATTERNS

    def analyze_diff(diff):
        lines = diff.split('\\n')
    """
    print(generate_commit_message(sample_diff, provider="ollama"))
