import json
from typing import Dict, Any, Optional
from pathlib import Path
import jsonschema
from jsonschema import validate
from gitmuse.utils.logging import configure_logging, get_logger

# Default configuration
DEFAULT_CONFIG = {
    "version": 1,
    "ai": {
        "provider": "ollama",
        "openai": {"model": "gpt-4o", "apiKey": "", "organizationId": ""},
        "ollama": {"model": "llama3.1", "url": "http://localhost:11434"},
    },
    "commit": {
        "style": "conventional",
        "maxLength": 72,
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
    },
    "prompts": {"commitMessage": {"useDefault": True, "customTemplate": ""}},
    "logging": {"level": "INFO", "format": "console", "file": None},
}

SCHEMA_PATH = Path(__file__).parent.parent.parent / "gitmuse-schema.json"


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


class Config:
    def __init__(self):
        self.config = self.load_config()
        self.setup_logging()
        self.logger = get_logger(__name__)

    def setup_logging(self):
        log_level = self.config["logging"]["level"]
        log_format = self.config["logging"]["format"]
        log_file = self.config["logging"]["file"]
        configure_logging(log_level, log_format, log_file)

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

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from gitmuse.json file or use default values."""
        config = DEFAULT_CONFIG.copy()
        repo_root = self.find_repository_root()
        possible_paths = [
            repo_root / "gitmuse.json" if repo_root else None,
            Path.home() / "gitmuse.json",
        ]

        for config_path in possible_paths:
            if config_path and config_path.exists():
                try:
                    user_config = json.loads(config_path.read_text())
                    schema = self.load_schema()
                    if schema:
                        validate(instance=user_config, schema=schema)
                    config.update(user_config)
                    print(f"Loaded configuration from {config_path}")
                    break
                except (
                    json.JSONDecodeError,
                    jsonschema.exceptions.ValidationError,
                ) as e:
                    print(
                        f"Warning: Invalid configuration in {config_path}. Using default configuration. Error: {e}"
                    )

        return config

    def get_nested_config(self, *keys: str) -> Any:
        """Get a nested configuration value."""
        value = self.config
        for key in keys:
            value = value.get(key)
            if value is None:
                error_msg = f"Configuration key not found: {'.'.join(keys)}"
                self.logger.error(error_msg)
                raise ConfigError(error_msg)
        return value

    def get_ai_provider(self) -> str:
        return self.get_nested_config("ai", "provider")

    def get_ai_model(self) -> str:
        provider = self.get_ai_provider()
        return self.get_nested_config("ai", provider, "model")

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
