import json
from pathlib import Path
from typing import Any, Dict, Optional
from typing_extensions import TypedDict

import jsonschema  # type: ignore
from pydantic import BaseModel
from gitmuse.utils.logging import configure_logging, get_logger

# Define typed dictionaries for our configuration structure
class OpenAIConfig(TypedDict, total=False):
    model: str
    apiKey: str
    organizationId: str
    max_tokens: int
    temperature: float


class OllamaConfig(TypedDict, total=False):
    model: str
    url: str
    max_tokens: int
    temperature: float


class AIConfigDict(TypedDict, total=False):
    provider: str
    openai: OpenAIConfig
    ollama: OllamaConfig


class CommitConfigDict(TypedDict):
    style: str
    maxLength: int
    includeScope: bool
    includeBody: bool
    includeFooter: bool
    conventionalCommitTypes: Dict[str, str]


class PromptsConfigDict(TypedDict):
    commitMessage: Dict[str, Any]


class LoggingConfigDict(TypedDict):
    level: str
    format: str
    file: Optional[str]


class ConfigDict(TypedDict):
    version: int
    ai: AIConfigDict
    commit: CommitConfigDict
    prompts: PromptsConfigDict
    logging: LoggingConfigDict


# Define default models
DEFAULT_OPENAI_CONFIG: OpenAIConfig = {
    "model": "gpt-4o",
    "apiKey": "",
    "organizationId": "",
    "max_tokens": 1000,
    "temperature": 0.7,
}

DEFAULT_OLLAMA_CONFIG: OllamaConfig = {
    "model": "gemma2:27b",
    "url": "http://localhost:11434",
    "max_tokens": 1000,
    "temperature": 0.7,
}

DEFAULT_COMMIT_CONFIG: CommitConfigDict = {
    "style": "conventional",
    "maxLength": 500,
    "includeScope": True,
    "includeBody": True,
    "includeFooter": True,
    "conventionalCommitTypes": {
        "feat": "✨",
        "fix": "🐛",
        "docs": "📝",
        "style": "💎",
        "refactor": "♻️",
        "perf": "⚡",
        "test": "🧪",
        "build": "🏗️",
        "ci": "🚀",
        "chore": "🧹",
    },
}

DEFAULT_PROMPTS_CONFIG: PromptsConfigDict = {
    "commitMessage": {"useDefault": True, "customTemplate": ""}
}

DEFAULT_LOGGING_CONFIG: LoggingConfigDict = {
    "level": "INFO",
    "format": "console",
    "file": "",
}

# Default configuration
DEFAULT_CONFIG: ConfigDict = {
    "version": 1,
    "ai": {
        "provider": "ollama",
        "openai": DEFAULT_OPENAI_CONFIG,
        "ollama": DEFAULT_OLLAMA_CONFIG,
    },
    "commit": DEFAULT_COMMIT_CONFIG,
    "prompts": DEFAULT_PROMPTS_CONFIG,
    "logging": DEFAULT_LOGGING_CONFIG,
}

SCHEMA_PATH = Path(__file__).parent / "gitmuse-schema.json"


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


class AIConfig(BaseModel):
    provider: str
    openai: Optional[OpenAIConfig] = None
    ollama: Optional[OllamaConfig] = None

class CommitConfig(BaseModel):
    style: str
    maxLength: int
    includeScope: bool
    includeBody: bool
    includeFooter: bool
    conventionalCommitTypes: Dict[str, str]

class PromptsConfig(BaseModel):
    commitMessage: Dict[str, Any]

class LoggingConfig(BaseModel):
    level: str
    format: str
    file: Optional[str] = None

class ConfigModel(BaseModel):
    version: int
    ai: AIConfig
    commit: CommitConfig
    prompts: PromptsConfig
    logging: LoggingConfig


class Config:
    """
    Configuration manager for GitMuse.
    Loads and validates the configuration from a JSON file and provides access to the configuration values.
    """

    def __init__(self):
        self.config = self.load_config()
        self.setup_logging()
        self.logger = get_logger(__name__)

    def setup_logging(self):
        log_config = self.config.logging
        configure_logging(
            log_level=log_config.level,
            log_format=log_config.format,
            log_file=log_config.file,
            use_rich=True  # Puedes ajustar esto según tus preferencias
        )

    def load_schema(self) -> Optional[Dict[str, Any]]:
        if SCHEMA_PATH.exists():
            with SCHEMA_PATH.open("r") as f:
                return json.load(f)
        print(f"Warning: Schema file not found at {SCHEMA_PATH}")
        return None

    @staticmethod
    def find_repository_root(start_path: Path = Path.cwd()) -> Optional[Path]:
        """Find the root of the git repository."""
        current_path = start_path.resolve()
        while current_path != current_path.parent:
            if (current_path / ".git").exists():
                return current_path
            current_path = current_path.parent
        return None

    def load_config(self) -> ConfigModel:
        config_dict: ConfigDict = DEFAULT_CONFIG.copy()
        possible_paths = [
            Path.cwd() / "gitmuse.json",
            Path.home() / ".config" / "gitmuse" / "gitmuse.json",
            Path("/etc/gitmuse/gitmuse.json"),
        ]

        for config_path in possible_paths:
            if config_path.exists():
                try:
                    user_config = json.loads(config_path.read_text())
                    schema = self.load_schema()
                    if schema:
                        jsonschema.validate(instance=config_dict, schema=schema)
                    config_dict.update(user_config)
                    print(f"Loaded configuration from {config_path}")
                    break
                except (json.JSONDecodeError, jsonschema.exceptions.ValidationError) as e:
                    raise ConfigError(f"Invalid configuration: {str(e)}")

        return ConfigModel(
            version=config_dict["version"],
            ai=AIConfig(**config_dict["ai"]),
            commit=CommitConfig(**config_dict["commit"]),
            prompts=PromptsConfig(**config_dict["prompts"]),
            logging=LoggingConfig(**config_dict["logging"])
        )

    def get_nested_config(self, *keys: str) -> Any:
        """Get a nested configuration value."""
        value = self.config.model_dump() 
        for key in keys:
            try:
                value = value[key]
            except KeyError:
                self.logger.error(f"Configuration key '{key}' not found.")
                raise ConfigError(f"Configuration key '{key}' not found.")
        return value

    def get_ai_provider(self) -> str:
        return self.get_nested_config("ai", "provider")

    def get_ai_model(self) -> str:
        provider = self.get_ai_provider()
        return self.get_nested_config("ai", provider, "model")

    def get_max_tokens(self) -> int:
        provider = self.get_ai_provider()
        return self.get_nested_config("ai", provider, "max_tokens")

    def get_temperature(self) -> float:
        provider = self.get_ai_provider()
        return self.get_nested_config("ai", provider, "temperature")

    def get_openai_api_key(self) -> str:
        return self.get_nested_config("ai", "openai", "apiKey")

    def get_openai_organization_id(self) -> str:
        return self.get_nested_config("ai", "openai", "organizationId")

    def get_ollama_url(self) -> str:
        return self.get_nested_config("ai", "ollama", "url")

    def get_commit_style(self) -> str:
        return self.get_nested_config("commit", "style")

    def get_max_message_length(self) -> int:
        return self.get_nested_config("commit", "maxLength")

    def get_include_scope(self) -> bool:
        return self.get_nested_config("commit", "includeScope")

    def get_include_body(self) -> bool:
        return self.get_nested_config("commit", "includeBody")

    def get_include_footer(self) -> bool:
        return self.get_nested_config("commit", "includeFooter")

    def get_conventional_commit_types(self) -> Dict[str, str]:
        return self.get_nested_config("commit", "conventionalCommitTypes")

    def get_commit_message_template(self) -> str:
        return self.get_nested_config("prompts", "commitMessage", "customTemplate")

    def get_log_level(self) -> str:
        return self.get_nested_config("logging", "level")

    def get_log_format(self) -> str:
        return self.get_nested_config("logging", "format")

    def get_log_file(self) -> Optional[str]:
        return self.get_nested_config("logging", "file")

    def init_config(self, path: Optional[Path] = None) -> None:
        """Initialize a new configuration file."""
        if path is None:
            repo_root = self.find_repository_root()
            path = (
                repo_root / "gitmuse.json"
                if repo_root
                else Path.home() / "gitmuse.json"
            )

        if path.exists():
            self.logger.warning(f"Configuration file already exists at {path}")
            return

        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
        self.logger.info(f"Initialized default configuration at {path}")


# Load the configuration
CONFIG = Config()