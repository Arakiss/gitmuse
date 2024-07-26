import os
from typing import Dict, List, Optional
from pydantic import BaseModel
from gitmuse.core.diff_analyzer import analyze_diff
from gitmuse.config.settings import CONFIG
from gitmuse.providers.openai import OpenAIProvider
from gitmuse.providers.ollama import OllamaProvider
from gitmuse.providers.base import (
    AIProvider,
    AIProviderConfig,
    OpenAIConfig,
    OllamaConfig,
)
from rich.console import Console

console = Console()


class Changes(BaseModel):
    files_summary: str
    changes_summary: str
    detailed_changes: List[str]


def get_provider(provider: Optional[str] = None) -> AIProvider:
    providers: Dict[str, type[AIProvider]] = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
    }
    provider_name = provider or CONFIG.get_ai_provider()
    provider_class = providers.get(provider_name)
    if provider_class is None:
        raise ValueError(f"Unsupported provider specified: {provider_name}")

    model = CONFIG.get_ai_model()
    max_tokens = CONFIG.get_max_tokens()
    temperature = CONFIG.get_temperature()

    config: AIProviderConfig
    if provider_name == "openai":
        api_key = CONFIG.get_openai_api_key()
        config = OpenAIConfig(
            model=model, max_tokens=max_tokens, temperature=temperature, api_key=api_key
        )
        provider_instance = provider_class(config)
        if isinstance(provider_instance, OpenAIProvider):
            provider_instance.client = OpenAIProvider.configure(api_key)
        return provider_instance
    elif provider_name == "ollama":
        url = CONFIG.get_ollama_url()
        config = OllamaConfig(
            model=model, max_tokens=max_tokens, temperature=temperature, url=url
        )
        provider_instance = provider_class(config)
        return provider_instance
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")


def load_default_template() -> str:
    default_template = """
    Generate a semantic commit message for the following changes:
    Files changed: {files_summary}
    Summary: {changes_summary}

    Detailed changes:
    {detailed_changes}

    Follow these guidelines strictly:
    1. Use one of the following commit types: {keywords}
    2. Format: <type>[optional scope]: <description>
    3. The description should be in lowercase and not end with a period
    4. Keep the first line (header) under 50 characters
    5. After the header, add a blank line followed by a more detailed description
    6. In the description, explain the 'what' and 'why' of the changes, not the 'how'
    7. Use bullet points (- ) for multiple lines in the description
    8. Do not include file names or technical details unless absolutely necessary

    Format the message exactly like this:
    type(optional scope): short description

    - Detailed explanation of the changes
    - Reason for the changes
    - Any breaking changes (if applicable)

    IMPORTANT: Provide ONLY the commit message, no additional text or explanations.
    """
    return default_template


def create_prompt_content(
    changes: Changes,
    use_default_template: bool = True,
    custom_template: str = "",
) -> str:
    commit_types = CONFIG.get_conventional_commit_types()
    keywords = ", ".join([f"{emoji} {verb}" for verb, emoji in commit_types.items()])
    template = custom_template if not use_default_template else load_default_template()

    return template.format(
        files_summary=changes.files_summary,
        changes_summary=changes.changes_summary,
        detailed_changes=" ".join(changes.detailed_changes),
        keywords=keywords,
    )


def generate_commit_message(
    diff: str,
    provider: Optional[str] = None,
    use_default_template: bool = True,
    custom_template: str = "",
) -> str:
    try:
        changes_dict = analyze_diff(diff)
        changes = summarize_changes(changes_dict)
        prompt_content = create_prompt_content(
            changes, use_default_template, custom_template
        )
        provider_instance = get_provider(provider)
        return provider_instance.generate_commit_message(prompt_content)
    except Exception as e:
        console.print(f"[bold red]Error generating commit message: {str(e)}[/bold red]")
        return (
            "📝 Update files\n\nAn error occurred while generating the commit message."
        )


def summarize_changes(changes: Dict[str, List[Dict[str, str]]]) -> Changes:
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
    detailed_changes = generate_detailed_changes(changes)
    return Changes(
        files_summary=files_summary,
        changes_summary=changes_summary,
        detailed_changes=detailed_changes,
    )


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
    print(generate_commit_message(sample_diff))
