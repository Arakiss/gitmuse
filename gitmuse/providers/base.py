from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    def generate_commit_message(self, prompt: str) -> str:
        pass
