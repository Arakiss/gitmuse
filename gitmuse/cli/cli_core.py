import os
from rich.console import Console
from gitmuse.config.settings import DEFAULT_PROVIDER
from gitmuse.cli.commands import commit_command
from gitmuse.providers.openai import OpenAIProvider
from gitmuse.providers.ollama import OllamaProvider

console = Console()


def run_cli() -> None:
    """
    Run the command-line interface (CLI) to handle commits based on the specified provider.
    Checks the provider environment variable and configures the corresponding provider (OpenAI or Ollama).
    Raises errors if the provider is unsupported, API key is missing for OpenAI, or Ollama is not accessible.
    """
    try:
        provider = os.getenv("PROVIDER", DEFAULT_PROVIDER)

        if provider == "openai":
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise RuntimeError(
                    "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
                )
            OpenAIProvider.configure(openai_api_key)
        elif provider == "ollama":
            if not OllamaProvider.check_ollama():
                raise RuntimeError(
                    "Ollama is not running or not accessible. Please start Ollama and try again."
                )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        commit_command(provider)

    except (RuntimeError, ValueError) as e:
        console.print(f":x: [bold red]Error:[/bold red] {e}")
