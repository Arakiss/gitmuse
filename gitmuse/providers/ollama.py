from functools import lru_cache
from typing import Optional, Dict, Any
from gitmuse.providers.base import BaseProvider
import ollama
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

console = Console()


@lru_cache(maxsize=1)
def get_ollama_status() -> Optional[Dict[str, Any]]:
    try:
        return ollama.ps()
    except Exception as e:
        console.print(f"[bold red]Error checking Ollama status: {e}[/bold red]")
        return None


class OllamaProvider(BaseProvider):
    def __init__(self, model_name: str = "llama3.1"):
        self.model_name = model_name
        self.status = get_ollama_status()

    def generate_commit_message(self, prompt: str) -> str:
        if not self.status:
            return "📝 Update files\n\nOllama is not running or not accessible."

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Generating commit message...", total=None)

            try:
                formatted_prompt = self.format_prompt_for_llama(prompt)
                response = ollama.generate(
                    model=self.model_name,
                    prompt=formatted_prompt,
                    options={
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_predict": 256,
                    },
                )
                progress.update(task, completed=True)

                generated_message = self.process_ollama_response(response)
                return generated_message
            except Exception as e:
                progress.update(task, completed=True)
                console.print(
                    f"[bold red]Error generating commit message with Ollama: {e}[/bold red]"
                )
                return "📝 Update files\n\nSummary of changes."

    def process_ollama_response(self, response: Dict[str, Any]) -> str:
        console.print("[bold green]Ollama response metadata:[/bold green]")
        console.print(f"  Model: {response.get('model', 'Unknown')}")
        console.print(f"  Created at: {response.get('created_at', 'Unknown')}")
        console.print(
            f"  Total duration: {response.get('total_duration', 'Unknown')} ns"
        )

        generated_message = response.get("response", "").strip()
        if not generated_message:
            return "📝 Update files\n\nSummary of changes."
        return generated_message.split("<|eot_id|>")[0].strip()

    @staticmethod
    def format_prompt_for_llama(prompt: str) -> str:
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant for generating git commit messages. Your task is to create concise, informative, and well-structured commit messages based on the provided diff information.

Guidelines for generating commit messages:
1. Start with an emoji that represents the type of change.
2. Use an imperative present tense verb to describe the main action.
3. Keep the first line (summary) under 50 characters.
4. Provide more details in subsequent lines, if necessary.
5. Use bullet points for multiple changes.
6. Focus on the 'why' behind the changes, not just the 'what'.
7. Mention any breaking changes prominently.

<|eot_id|><|start_header_id|>user<|end_header_id|>

{prompt}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

    @staticmethod
    def check_ollama() -> bool:
        status = get_ollama_status()
        return status is not None

    def __repr__(self) -> str:
        return f"OllamaProvider(model_name='{self.model_name}', status={'Available' if self.status else 'Unavailable'})"


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
    provider = OllamaProvider()
    print(provider.generate_commit_message(sample_diff))
