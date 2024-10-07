import subprocess
from typing import Dict, Any, List
from gitmuse.providers.base import AIProvider, AIProviderConfig
from gitmuse.utils.logging import get_logger
from gitmuse.config.settings import CONFIG
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import requests  # type: ignore
import json
import re

logger = get_logger(__name__)
console = Console()


class OpenAIProvider(AIProvider):
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or CONFIG.get_openai_api_key()  # type: ignore
        self.model = config.model or CONFIG.get_ai_model() or "gpt-4o"
        self.url = "https://api.openai.com/v1/chat/completions"
        logger.info(f"Initialized OpenAIProvider with model {self.model}")

    def generate_commit_message(self, prompt: str) -> str:
        """
        Generate a commit message using the OpenAI API based on the given prompt.
        """
        if not self.api_key:
            logger.error("OpenAI API key is not set.")
            return "📝 Update files\n\nOpenAI API key is not set."

        logger.info("Generating commit message with OpenAI")
        progress = Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console)
        with progress:
            task = progress.add_task("[cyan]Generating commit message...", total=None)
            try:
                response = self.make_api_request(prompt)
                progress.update(task, completed=True)
                return self.process_openai_response(response)
            except Exception as e:
                progress.update(task, completed=True)
                logger.error(f"Error generating commit message with OpenAI: {e}", exc_info=True)
                console.print(f"[bold red]Error:[/bold red] Failed to generate commit message. Details: {e}")
                return "📝 Update files\n\nFailed to generate commit message due to an error."

    def make_api_request(self, prompt: str) -> Dict[str, Any]:
        """
        Make a request to the OpenAI API.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        response = requests.post(self.url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def process_openai_response(self, response: Dict[str, Any]) -> str:
        """
        Process the response from the OpenAI API.
        """
        content = response['choices'][0]['message']['content']
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            content = match.group()
        else:
            raise ValueError("Unable to extract JSON content from the response")
        commit_data = json.loads(content)
        return self.format_commit_message(commit_data)

    def format_commit_message(self, commit_data: Dict[str, Any]) -> str:
        """
        Format the commit message based on the generated data.
        """
        title = commit_data['title'][:50]
        body = commit_data['body']
        summary = commit_data['summary']

        formatted_message = f"{title}\n\n"
        for category, content in body.items():
            formatted_message += f"{content['emoji']} {category}:\n"
            for change in content['changes']:
                formatted_message += f"- {change}\n"
            formatted_message += "\n"
        
        formatted_message += f"{summary}\n"

        return formatted_message

    def display_progress(self, message: str):
        return console.status(f"[bold green]{message}[/bold green]")

def get_diff() -> str:
    """Get the current git diff."""
    return subprocess.check_output(['git', 'diff', '--staged']).decode('utf-8')

def get_changed_files() -> List[str]:
    """Get the list of changed files."""
    return subprocess.check_output(['git', 'diff', '--staged', '--name-only']).decode('utf-8').splitlines()

def generate_prompt(diff: str, changed_files: List[str]) -> str:
    """Generate the prompt for the OpenAI API."""
    files_summary = ", ".join(changed_files[:3])
    if len(changed_files) > 3:
        files_summary += f" and {len(changed_files) - 3} more"

    commit_config = CONFIG.config.commit
    commit_types = commit_config.conventionalCommitTypes

    return f"""Generate a structured commit message for the following git diff, following the semantic commit and gitemoji conventions:

Files changed: {files_summary}

```
{diff}
```

Requirements:
1. Title: Maximum {commit_config.maxLength} characters, starting with an appropriate gitemoji, followed by the semantic commit type and a brief description.
2. Body: Organize changes into categories. Each category should have an appropriate emoji and 2-3 bullet points summarizing key changes.
3. Summary: A brief sentence summarizing the overall impact of the changes.

Use one of the following types with their corresponding emojis: 
{', '.join([f"{emoji} {verb}" for verb, emoji in commit_types.items()])}

Respond in the following JSON format:
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

Ensure that each category and change is relevant and specific to the diff provided. Use appropriate and varied emojis for different categories.
"""

if __name__ == "__main__":
    config = AIProviderConfig(
        model=CONFIG.get_ai_model() or "gpt-4o",
        max_tokens=CONFIG.get_max_tokens() or 300,
        temperature=CONFIG.get_temperature() or 0.7,
        api_key=CONFIG.get_openai_api_key(),  # type: ignore
    )
    provider = OpenAIProvider(config)

    changed_files = get_changed_files()
    if not changed_files:
        console.print("\n[bold red]🌚 No changes detected in the staging area.[/bold red]")
    else:
        diff = get_diff()
        prompt = generate_prompt(diff, changed_files)
        commit_message = provider.generate_commit_message(prompt)
        console.print(f"\n[bold green]Generated commit message:[/bold green]\n\n{commit_message}")