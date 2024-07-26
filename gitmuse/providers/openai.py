from gitmuse.providers.base import AIProvider, AIProviderConfig
from openai import OpenAI
from rich.console import Console

console = Console()


class OpenAIProvider(AIProvider):
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.client = None

    @staticmethod
    def configure(api_key: str):
        return OpenAI(api_key=api_key)

    def generate_commit_message(self, prompt: str) -> str:
        with self.display_progress("Generating commit message...") as progress:
            task = progress.add_task("[cyan]Generating commit message...", total=None)
            try:
                if not self.client:
                    raise ValueError(
                        "OpenAI client is not configured. Call configure() first."
                    )

                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that generates commit messages.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=self.config.max_tokens,
                    n=1,
                    temperature=self.config.temperature,
                )
                progress.update(task, completed=True)
                return response.choices[0].message.content.strip()
            except Exception as e:
                progress.update(task, completed=True)
                console.print(
                    f"[bold red]Error generating commit message with OpenAI: {e}[/bold red]"
                )
                return "📝 Update files\n\nSummary of changes."


if __name__ == "__main__":
    import os
    from gitmuse.config.settings import CONFIG

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")

    config = AIProviderConfig(
        model=CONFIG.get_ai_model(), max_tokens=300, temperature=0.7
    )
    provider = OpenAIProvider(config)
    provider.client = OpenAIProvider.configure(api_key)

    sample_prompt = "Generate a commit message for adding a new feature that allows users to export data in CSV format."
    print(provider.generate_commit_message(sample_prompt))
