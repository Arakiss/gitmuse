from abc import ABC, abstractmethod
from typing import Any, Dict, Generator
from pydantic import BaseModel, Field
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

console = Console()


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers.
    """
    @abstractmethod
    def generate_commit_message(self, prompt: str) -> str:
        """
        Generate a commit message based on the given prompt.
        """
        pass


class AIProviderConfig(BaseModel):
    """
    Configuration settings common to all AI providers.
    """
    model: str
    max_tokens: int = Field(default=300, ge=1)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)


class AIProvider(BaseProvider):
    """
    Base class for AI providers, providing common functionality.
    """
    def __init__(self, config: AIProviderConfig, **kwargs: Any):
        self.config = config
        self.extra_config: Dict[str, Any] = kwargs

    def display_progress(self, task_description: str) -> Generator[Progress, None, None]:
        """
        Display a progress spinner for long-running tasks.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[progress.description]{task_description}"),
            console=console,
        ) as progress:
            yield progress

    @abstractmethod
    def generate_commit_message(self, prompt: str) -> str:
        """
        Abstract method to generate a commit message.
        """
        pass


class OpenAIConfig(AIProviderConfig):
    """
    Configuration settings specific to the OpenAI provider.
    """
    api_key: str


class OllamaConfig(AIProviderConfig):
    """
    Configuration settings specific to the Ollama provider.
    """
    url: str
