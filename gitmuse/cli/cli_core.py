import os
import click
from rich.console import Console
from gitmuse.config.settings import CONFIG
from gitmuse.cli.commands import commit_command
from gitmuse.providers.openai import OpenAIProvider
from gitmuse.providers.ollama import OllamaProvider

console = Console()


@click.group()
def cli():
    """GitMuse CLI"""
    pass


@cli.command()
def commit():
    """Generate and apply a commit message"""
    run_commit()


@cli.command()
@click.option(
    "--global", "is_global", is_flag=True, help="Initialize global configuration"
)
def init(is_global):
    """Initialize GitMuse configuration"""
    if is_global:
        CONFIG.init_config(os.path.expanduser("~/gitmuse.json"))
    else:
        CONFIG.init_config()


def run_commit() -> None:
    """
    Run the commit command based on the specified provider.
    Checks the provider environment variable and configures the corresponding provider (OpenAI or Ollama).
    Raises errors if the provider is unsupported, API key is missing for OpenAI, or Ollama is not accessible.
    """
    try:
        provider = os.getenv("PROVIDER", CONFIG.get_ai_provider())

        if provider == "openai":
            openai_api_key = os.getenv("OPENAI_API_KEY") or CONFIG.get_openai_api_key()
            if not openai_api_key:
                raise RuntimeError(
                    "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable or in the configuration file."
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


def run_cli():
    cli()


if __name__ == "__main__":
    run_cli()
