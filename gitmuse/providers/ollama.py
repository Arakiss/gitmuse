from functools import lru_cache
from typing import Optional, Dict, Any
from gitmuse.providers.base import AIProvider
import ollama
from gitmuse.utils.logging import get_logger
from gitmuse.config.settings import CONFIG

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_ollama_status() -> Optional[Dict[str, Any]]:
    try:
        return ollama.ps()
    except Exception as e:
        logger.error(f"Error checking Ollama status: {e}")
        return None


class OllamaProvider(AIProvider):
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name or CONFIG.get_ai_model())
        self.status = get_ollama_status()
        self.url = CONFIG.get_ollama_url()
        logger.info(f"Initialized OllamaProvider with model {self.model}")

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
                    model=self.model,
                    prompt=formatted_prompt,
                    options=self.get_generation_options(),
                )
                progress.update(task, completed=True)
                return self.process_ollama_response(response)
            except Exception as e:
                progress.update(task, completed=True)
                logger.error(f"Error generating commit message with Ollama: {e}")
                return "📝 Update files\n\nSummary of changes."

    @staticmethod
    def get_generation_options() -> Dict[str, Any]:
        return {
            "temperature": 0.6,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 256,
        }

    @staticmethod
    def format_prompt_for_llama(prompt: str) -> str:
        system_message = """You are an AI assistant specialized in generating git commit messages. Your task is to create concise, informative, and well-structured commit messages based on the provided information.

Guidelines for generating commit messages:
1. Start with an emoji that represents the type of change, followed by an imperative present tense verb.
2. Keep the first line (summary) under 50 characters, including the emoji.
3. Leave a blank line after the summary.
4. Provide 2-3 bullet points explaining key changes, each starting with a dash (-).
5. Focus on the 'what' and 'why' of the changes, not the 'how'.
6. Do not include file names or technical details unless absolutely necessary.
7. Do not add any notes, explanations, or comments about the commit message itself.

Format the message exactly like this:
🎨 Verb Summary of changes

- Key change 1
- Key change 2
- Key change 3 (if necessary)

Respond ONLY with the commit message, no additional text or explanations."""

        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{system_message}<|eot_id|><|start_header_id|>user<|end_header_id|>
{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

    def process_ollama_response(self, response: Dict[str, Any]) -> str:
        generated_message = response.get("response", "").strip()
        if not generated_message:
            logger.warning("Ollama returned an empty response")
            return "📝 Update files\n\nSummary of changes."

        lines = generated_message.split("\n")
        cleaned_lines = [
            line
            for line in lines
            if not line.startswith("Note:") and not line.startswith("IMPORTANT:")
        ]
        return "\n".join(cleaned_lines).strip()

    @classmethod
    def check_ollama(cls) -> bool:
        status = get_ollama_status()
        if status is None:
            logger.warning("Ollama is not available")
        else:
            logger.info("Ollama is available")
        return status is not None

    def __repr__(self) -> str:
        return f"OllamaProvider(model_name='{self.model}', status={'Available' if self.status else 'Unavailable'}, url='{self.url}')"


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
        lines = diff.split('\n')
    """
    provider = OllamaProvider()
    commit_message = provider.generate_commit_message(sample_diff)
    logger.info(f"Generated commit message:\n{commit_message}")
