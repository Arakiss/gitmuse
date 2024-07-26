from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel, Field
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

console = Console()


class BaseProvider(ABC):
    @abstractmethod
    def generate_commit_message(self, prompt: str) -> str:
        pass


class AIProviderConfig(BaseModel):
    model: str
    max_tokens: int = Field(default=300, ge=1)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)


class AIProvider(BaseProvider):
    def __init__(self, config: AIProviderConfig, **kwargs: Any):
        self.config = config
        self.extra_config: Dict[str, Any] = kwargs

    def display_progress(self, task_description: str):
        return Progress(
            SpinnerColumn(),
            TextColumn(f"[progress.description]{task_description}"),
            console=console,
        )

    @abstractmethod
    def generate_commit_message(self, prompt: str) -> str:
        pass


class OpenAIConfig(AIProviderConfig):
    api_key: str


class OllamaConfig(AIProviderConfig):
    url: str
