import os
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel
from gitmuse.core.diff_analyzer import analyze_diff
from gitmuse.config.settings import CONFIG
from gitmuse.providers.openai import OpenAIProvider
from gitmuse.providers.ollama import OllamaProvider
from gitmuse.providers.base import (
    AIProvider,
    OpenAIConfig,
    OllamaConfig,
)
from gitmuse.utils.logging import get_logger
from rich.console import Console
import json
import re

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

    provider = provider or CONFIG.get_ai_provider()
    provider_class = providers.get(provider)

    if not provider_class:
        raise ValueError(f"Unsupported AI provider: {provider}")

    if provider == "openai":
        config: Union[OpenAIConfig, OllamaConfig] = OpenAIConfig(
            model=CONFIG.get_ai_model(),
            max_tokens=CONFIG.get_max_tokens(),
            temperature=CONFIG.get_temperature(),
            api_key=CONFIG.get_openai_api_key(),
        )
    elif provider == "ollama":
        config = OllamaConfig(
            model=CONFIG.get_ai_model(),
            max_tokens=CONFIG.get_max_tokens(),
            temperature=CONFIG.get_temperature(),
            url=CONFIG.get_ollama_url(),
        )
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")

    return provider_class(config)



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
    Generate a structured commit message for the following changes, following the semantic commit and gitemoji conventions:

    Files changed: {files_summary}
    Summary: {changes_summary}

    Detailed changes:
    {detailed_changes}

    Requirements:
    1. Title: Maximum 50 characters, starting with an appropriate gitemoji, followed by the semantic commit type and a brief description.
    2. Body: Organize changes into categories. Each category should have an appropriate emoji and 2-3 bullet points summarizing key changes.
    3. Summary: A brief sentence summarizing the overall impact of the changes.
    4. For small changes (e.g., adding or removing a single line), focus on the purpose of the change rather than just describing the modification.

    Use one of the following commit types: {keywords}

    IMPORTANT: Respond ONLY with a JSON object in the following format. Do not include any other text or explanations:
    {{
        "title": "Your commit message title here",
        "body": {{
            "Category1": {{
                "emoji": "🔧",
                "changes": [
                    "First change in category 1",
                    "Second change in category 1"
                ]
            }},
            "Category2": {{
                "emoji": "✨",
                "changes": [
                    "First change in category 2",
                    "Second change in category 2"
                ]
            }}
        }},
        "summary": "A brief summary of the overall changes and their impact."
    }}

    Ensure that each category and change is relevant and specific to the changes provided. Use appropriate and varied emojis for different categories.
    For very small changes, focus on the intent or purpose of the change, not just the literal modification.
    IMPORTANT: Provide ONLY the JSON response, no additional text or explanations.
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
    use_default_template: Optional[bool] = None,
    custom_template: Optional[str] = None,
) -> str:
    try:
        changes_dict = analyze_diff(diff)
        logger.debug(f"Analyzed diff: {changes_dict}")
        changes = summarize_changes(changes_dict)
        logger.debug(f"Summarized changes: {changes}")
        
        template_config = CONFIG.get_commit_message_template()
        
        if isinstance(template_config, tuple):
            use_default = use_default_template if use_default_template is not None else template_config[0]
            template = custom_template or template_config[1]
        else:
            use_default = use_default_template if use_default_template is not None else True
            template = custom_template or template_config
        
        prompt_content = create_prompt_content(
            changes, 
            use_default,
            template
        )
        logger.debug(f"Created prompt content: {prompt_content}")
        
        provider_instance = get_provider(provider)
        message_json = provider_instance.generate_commit_message(prompt_content)
        logger.info(f"Raw AI response: {message_json}")
        
        extracted_message = extract_message_from_raw_response(message_json)
        logger.info(f"Extracted message: {extracted_message}")
        
        if not extracted_message.strip():
            raise ValueError("Generated commit message is empty")
        
        return extracted_message
    except Exception as e:
        logger.exception(f"Error generating commit message: {str(e)}")
        return (
            "📝 Update files\n\nAn error occurred while generating the commit message. "
            f"Error details: {str(e)}"
        )


def summarize_changes(changes: Dict[str, List[Dict[str, str]]]) -> Changes:
    files_changed = list(
        set(change["file"] for category in changes.values() for change in category)
    )
    files_summary = ", ".join(files_changed[:5]) + (
        f" and {len(files_changed) - 5} more files" if len(files_changed) > 5 else ""
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
            file_type = "code" if file_ext in ['.py', '.js', '.ts', '.cpp', '.java'] else \
                        "documentation" if file_ext in ['.md', '.txt', '.rst'] else \
                        "configuration" if file_ext in ['.json', '.yaml', '.yml', '.toml'] else \
                        "unknown"
            
            change_description = f"{category.capitalize()} in {file_type} file {item['file']}: "
            if "content" in item:
                change_description += f"{item['content'][:100]}..."
            else:
                change_description += "File modified"
            detailed_changes.append(change_description)
    return detailed_changes


def format_commit_message(commit_data: Union[Dict[str, Any], str]) -> str:
    if isinstance(commit_data, str):
        return commit_data

    title = commit_data.get('title', 'Update files')[:50]
    body = commit_data.get('body', {})
    summary = commit_data.get('summary', 'Changes were made to the codebase.')

    formatted_message = f"{title}\n\n"
    if isinstance(body, dict):
        for category, content in body.items():
            if isinstance(content, dict):
                emoji = content.get('emoji', '📝')
                changes = content.get('changes', [])
                formatted_message += f"{emoji} {category}:\n"
                for change in changes:
                    formatted_message += f"- {change}\n"
            elif isinstance(content, list):
                formatted_message += f"📝 {category}:\n"
                for change in content:
                    formatted_message += f"- {change}\n"
            else:
                formatted_message += f"📝 {category}: {content}\n"
            formatted_message += "\n"
    elif isinstance(body, list):
        for item in body:
            formatted_message += f"{item}\n"
        formatted_message += "\n"
    elif isinstance(body, str):
        formatted_message += f"{body}\n\n"
    
    formatted_message += f"{summary}\n"

    return formatted_message.strip()


def extract_message_from_raw_response(raw_response: str) -> str:
    """
    Attempt to extract a usable commit message from a raw AI response.
    """
    # Remove any markdown code block indicators
    raw_response = re.sub(r'```(?:json)?\s*', '', raw_response)
    raw_response = raw_response.strip('`')

    # First, try to parse as JSON
    try:
        commit_data = json.loads(raw_response)
        return format_commit_message(commit_data)
    except json.JSONDecodeError:
        pass

    # If not JSON, try to extract structured information
    lines = raw_response.split('\n')
    title = ""
    body = []
    summary = ""
    current_section = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith(('💎', '✨', '⬆️', '🐛', '♻️', '📝', '🔧', '🚀')):
            if title:
                current_section = line
            else:
                title = line
        elif line.startswith('-'):
            body.append(f"{current_section}\n{line}")
        elif not summary and not line.startswith('-'):
            summary = line

    formatted_message = f"{title}\n\n" if title else ""
    formatted_message += "\n".join(body)
    formatted_message += f"\n\n{summary}" if summary else ""

    if not formatted_message.strip():
        # If we couldn't extract structured information, use the raw response as is
        formatted_message = raw_response

    return formatted_message.strip()


def format_non_json_response(raw_response: str) -> str:
    """
    Format a non-JSON response into a commit message.
    """
    lines = raw_response.split('\n')
    title = lines[0][:50] if lines else "Update files"
    body = "\n".join(lines[1:])
    return f"{title}\n\n{body}"


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