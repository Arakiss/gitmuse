import os
import json
from typing import Dict, Any
import jsonschema
from jsonschema import validate

# Default configuration
DEFAULT_CONFIG = {
    "version": 1,
    "ai": {
        "provider": "ollama",
        "openai": {"model": "gpt-3.5-turbo", "apiKey": "", "organizationId": ""},
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
}

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "gitmuse-schema.json")


class Config:
    def __init__(self):
        self.config = self.load_config()

    def load_schema(self):
        if os.path.exists(SCHEMA_PATH):
            with open(SCHEMA_PATH, "r") as f:
                return json.load(f)
        return None

    def find_repository_root(self, start_path=os.getcwd()):
        """Find the root of the git repository."""
        current_path = os.path.abspath(start_path)
        while current_path != "/":
            if os.path.exists(os.path.join(current_path, ".git")):
                return current_path
            current_path = os.path.dirname(current_path)
        return None

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from gitmuse.json file or use default values.
        """
        config = DEFAULT_CONFIG.copy()
        repo_root = self.find_repository_root()
        possible_paths = [
            os.path.join(repo_root, "gitmuse.json") if repo_root else None,
            os.path.expanduser("~/gitmuse.json"),
        ]

        for config_path in possible_paths:
            if config_path and os.path.exists(config_path):
                try:
                    with open(config_path, "r") as config_file:
                        user_config = json.load(config_file)
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

    def get_ai_provider(self) -> str:
        return self.config["ai"]["provider"]

    def get_ai_model(self) -> str:
        provider = self.get_ai_provider()
        return self.config["ai"][provider]["model"]

    def get_openai_api_key(self) -> str:
        return self.config["ai"]["openai"]["apiKey"]

    def get_openai_organization_id(self) -> str:
        return self.config["ai"]["openai"]["organizationId"]

    def get_ollama_url(self) -> str:
        return self.config["ai"]["ollama"]["url"]

    def get_commit_style(self) -> str:
        return self.config["commit"]["style"]

    def get_max_message_length(self) -> int:
        return self.config["commit"]["maxLength"]

    def get_include_scope(self) -> bool:
        return self.config["commit"]["includeScope"]

    def get_include_body(self) -> bool:
        return self.config["commit"]["includeBody"]

    def get_include_footer(self) -> bool:
        return self.config["commit"]["includeFooter"]

    def get_conventional_commit_types(self) -> Dict[str, str]:
        return self.config["commit"]["conventionalCommitTypes"]

    def get_commit_message_template(self) -> str:
        return self.config["prompts"]["commitMessage"].get("customTemplate", "")

    def init_config(self, path=None):
        """Initialize a new configuration file."""
        if path is None:
            repo_root = self.find_repository_root()
            path = (
                os.path.join(repo_root, "gitmuse.json")
                if repo_root
                else os.path.expanduser("~/gitmuse.json")
            )

        if os.path.exists(path):
            print(f"Configuration file already exists at {path}")
            return

        with open(path, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)

        print(f"Initialized default configuration at {path}")


# Load the configuration
CONFIG = Config()
