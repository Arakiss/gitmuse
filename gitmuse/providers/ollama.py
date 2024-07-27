from functools import lru_cache
from typing import Optional, Dict, Any, Mapping, cast
from gitmuse.providers.base import AIProvider, AIProviderConfig
import ollama
from gitmuse.utils.logging import get_logger
from gitmuse.config.settings import CONFIG
from rich.console import Console

logger = get_logger(__name__)
console = Console()


@lru_cache(maxsize=1)
def get_ollama_status() -> Optional[Dict[str, Any]]:
    try:
        return cast(Dict[str, Any], ollama.ps())
    except Exception as e:
        logger.error(f"Error checking Ollama status: {e}")
        return None


class OllamaProvider(AIProvider):
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.status = get_ollama_status()
        self.url = CONFIG.get_ollama_url() or "http://localhost:11434"
        logger.info(f"Initialized OllamaProvider with model {self.config.model}")

    def generate_commit_message(self, prompt: str) -> str:
        if not self.status:
            logger.warning("Ollama is not running or not accessible.")
            return "📝 Update files\n\nOllama is not running or not accessible."

        logger.info("Generating commit message with Ollama")
        with self.display_progress("Generating commit message...") as progress:
            task = progress.add_task("[cyan]Generating commit message...", total=None)
            try:
                formatted_prompt = self.format_prompt_for_llama(prompt)
                response = ollama.generate(
                    model=self.config.model,
                    prompt=formatted_prompt,
                    options=cast(ollama.Options, self.get_generation_options()),
                )
                progress.update(task, completed=True)
                return self.process_ollama_response(response)
            except Exception as e:
                progress.update(task, completed=True)
                logger.error(f"Error generating commit message with Ollama: {e}")
                return "📝 Update files\n\nSummary of changes."

    def get_generation_options(self) -> Dict[str, Any]:
        return {
            "temperature": self.config.temperature,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": self.config.max_tokens,
        }

    @staticmethod
    def format_prompt_for_llama(prompt: str) -> str:
        system_message = """You are an AI assistant specialized in generating semantic git commit messages. Your task is to create concise, informative, and well-structured commit messages based on the provided information.

Guidelines for generating semantic commit messages:
1. Always start with the appropriate emoji followed by the commit type
2. Use one of the following types with their corresponding emojis: 
   ✨ feat, 🐛 fix, 📝 docs, 💎 style, ♻️ refactor, ⚡ perf, 🧪 test, 🏗️ build, 🚀 ci, 🧹 chore
3. Format: <emoji> <type>[optional scope]: <description>
4. The description should be in lowercase and not end with a period
5. Keep the first line (header) under 50 characters
6. After the header, add a blank line followed by a more detailed description
7. In the description, explain the 'what' and 'why' of the changes, not the 'how'
8. Use bullet points (- ) for multiple lines in the description
9. For breaking changes, add BREAKING CHANGE: at the beginning of the footer or body section
10. Consider ALL changes in the diff when generating the commit message

Respond ONLY with the commit message, no additional text or explanations."""

        formatted_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{system_message}<|eot_id|><|start_header_id|>user<|end_header_id|>
Generate a commit message for the following changes:

{prompt}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        return formatted_prompt

    def process_ollama_response(self, response: Mapping[str, Any]) -> str:
        generated_message = response.get("response", "").strip()
        if not generated_message:
            logger.warning("Ollama returned an empty response")
            return "📝 Update files\n\nSummary of changes."

        # Remove any special tokens that might have been generated
        generated_message = generated_message.replace("<|eot_id|>", "").strip()

        lines = generated_message.split("\n")
        cleaned_lines = [
            line
            for line in lines
            if not line.startswith("Note:") and not line.startswith("IMPORTANT:")
        ]

        final_message = "\n".join(cleaned_lines).strip()
        logger.info(f"Processed Ollama response: {final_message}")
        return final_message

    @classmethod
    def check_ollama(cls) -> bool:
        status = get_ollama_status()
        if status is None:
            logger.warning("Ollama is not available")
        else:
            logger.info("Ollama is available")
        return status is not None

    def __repr__(self) -> str:
        return f"OllamaProvider(model_name='{self.config.model}', status={'Available' if self.status else 'Unavailable'}, url='{self.url}')"


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
    config = AIProviderConfig(
        model=CONFIG.get_ai_model() or "llama3.1",
        max_tokens=CONFIG.get_max_tokens() or 256,
        temperature=CONFIG.get_temperature() or 0.6,
    )
    provider = OllamaProvider(config)
    commit_message = provider.generate_commit_message(
        f"Updated diff analyzer with additional ignore patterns\n\nFull diff:\n{sample_diff}"
    )
    console.print(f"Generated commit message:\n{commit_message}")
