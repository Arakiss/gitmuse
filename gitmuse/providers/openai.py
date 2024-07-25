from gitmuse.providers.base import AIProvider
import openai
from rich.console import Console

console = Console()


class OpenAIProvider(AIProvider):
    def __init__(
        self, model: str = "gpt-4", max_tokens: int = 300, temperature: float = 0.7
    ):
        super().__init__(model, max_tokens, temperature)

    @staticmethod
    def configure(api_key: str):
        openai.api_key = api_key

    def generate_commit_message(self, prompt: str) -> str:
        with self.display_progress("Generating commit message...") as progress:
            task = progress.add_task("[cyan]Generating commit message...", total=None)
            try:
                response = openai.Completion.create(
                    model=self.model,
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    n=1,
                    stop=None,
                    temperature=self.temperature,
                )
                progress.update(task, completed=True)
                return response.choices[0].text.strip()
            except Exception as e:
                progress.update(task, completed=True)
                console.print(
                    f"[bold red]Error generating commit message with OpenAI: {e}[/bold red]"
                )
                return "📝 Update files\n\nSummary of changes."


if __name__ == "__main__":
    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")

    OpenAIProvider.configure(api_key)

    provider = OpenAIProvider()
    sample_prompt = "Generate a commit message for adding a new feature that allows users to export data in CSV format."
    print(provider.generate_commit_message(sample_prompt))
