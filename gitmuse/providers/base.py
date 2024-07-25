from abc import ABC, abstractmethod
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

console = Console()


class BaseProvider(ABC):
    @abstractmethod
    def generate_commit_message(self, prompt: str) -> str:
        pass


class AIProvider(BaseProvider):
    def __init__(self, model: str, max_tokens: int = 300, temperature: float = 0.7):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def display_progress(self, task_description: str):
        return Progress(
            SpinnerColumn(),
            TextColumn(f"[progress.description]{task_description}"),
            console=console,
        )
