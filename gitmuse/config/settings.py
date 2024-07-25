import os


def get_env_variable(var_name: str, default_value: str) -> str:
    """
    Get the environment variable or return a default value.

    :param var_name: Name of the environment variable.
    :param default_value: Default value to return if the environment variable is not set.
    :return: Value of the environment variable or the default value.
    """
    return os.getenv(var_name, default_value)


# Keywords and their corresponding emojis for commit messages
COMMIT_KEYWORDS = {
    "Add": "✨",
    "Drop": "🗑️",
    "Fix": "🐛",
    "Bump": "⬆️",
    "Make": "🛠️",
    "Start": "🎬",
    "Stop": "🛑",
    "Optimize": "⚡",
    "Document": "📝",
    "Refactor": "♻️",
    "Reformat": "🎨",
    "Rearrange": "🔀",
    "Redraw": "🖼️",
    "Reword": "✏️",
    "Revise": "📝",
    "Refresh": "🔄",
}

# Default provider for AI-powered features, can be overridden by an environment variable
DEFAULT_PROVIDER = get_env_variable("DEFAULT_PROVIDER", "ollama")  # 'ollama', 'openai'
