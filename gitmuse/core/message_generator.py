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
from gitmuse.utils.logging import get_logger
from rich.console import Console

console = Console()
logger = get_logger(__name__)


class Changes(BaseModel):
    files_summary: str
    changes_summary: str
    detailed_changes: List[str]


def get_provider(provider: Optional[str] = None) -> AIProvider:
    providers: Dict[str, type[AIProvider]] = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
    }
    provider_name = provider or CONFIG.get_ai_provider() or "ollama"
    provider_class = providers.get(provider_name)
    if provider_class is None:
        logger.warning(
            f"Unsupported provider specified: {provider_name}. Falling back to Ollama."
        )
        provider_name = "ollama"
        provider_class = OllamaProvider

    model = CONFIG.get_ai_model() or "llama3.1"
    max_tokens = CONFIG.get_max_tokens() or 1000
    temperature = CONFIG.get_temperature() or 0.7

    config: AIProviderConfig
    if provider_name == "openai":
        api_key = CONFIG.get_openai_api_key()
        if not api_key:
            raise ValueError("OpenAI API key is required but not provided.")
        config = OpenAIConfig(
            model=model, max_tokens=max_tokens, temperature=temperature, api_key=api_key
        )
        provider_instance = provider_class(config)
        if isinstance(provider_instance, OpenAIProvider):
            provider_instance.client = OpenAIProvider.configure(api_key)
    else:  # ollama
        url = CONFIG.get_ollama_url() or "http://localhost:11434"
        config = OllamaConfig(
            model=model, max_tokens=max_tokens, temperature=temperature, url=url
        )
        provider_instance = provider_class(config)

    return provider_instance


def load_template(provider: str) -> str:
    template_path = f"templates/{provider}_template.txt"
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as file:
            return file.read()
    else:
        if provider == "openai":
            return load_default_template()
        elif provider == "ollama":
            return OllamaProvider.format_prompt_for_llama(load_default_template())
        else:
            logger.warning(f"Unsupported provider: {provider}. Using default template.")
            return load_default_template()


def load_default_template() -> str:
    return """
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


def create_prompt_content(
    changes: Changes,
    use_default_template: bool = True,
    custom_template: str = "",
) -> str:
    commit_types = CONFIG.get_conventional_commit_types()
    keywords = ", ".join([f"{emoji} {verb}" for verb, emoji in commit_types.items()])
    provider = CONFIG.get_ai_provider() or "ollama"
    template = custom_template if not use_default_template else load_template(provider)

    detailed_changes = "\n".join(changes.detailed_changes)

    return template.format(
        files_summary=changes.files_summary,
        changes_summary=changes.changes_summary,
        detailed_changes=detailed_changes,
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
        logger.debug(f"Analyzed diff: {changes_dict}")
        changes = summarize_changes(changes_dict)
        logger.debug(f"Summarized changes: {changes}")
        prompt_content = create_prompt_content(
            changes, use_default_template, custom_template
        )
        logger.debug(f"Created prompt content: {prompt_content}")
        provider_instance = get_provider(provider)
        message = provider_instance.generate_commit_message(prompt_content)
        logger.info(f"Generated commit message: {message}")
        return message
    except Exception as e:
        logger.exception(f"Error generating commit message: {str(e)}")
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
