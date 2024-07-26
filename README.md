# GitMuse

GitMuse is an AI-powered tool that helps developers craft meaningful and descriptive Git commit messages. By analyzing your staged changes, GitMuse provides intelligent suggestions for your commit messages, making your Git history more informative and easier to navigate.

[![Release](https://github.com/Arakiss/gitmuse/actions/workflows/release.yml/badge.svg)](https://github.com/Arakiss/gitmuse/actions/workflows/release.yml)

## Features

- **AI-Powered Commit Messages**: Leverages OpenAI's GPT models or Ollama for locally hosted models to generate context-aware commit messages.
- **Git Integration**: Seamlessly integrates with your existing Git workflow.
- **Customizable**: Configure AI providers, commit message styles, and other preferences via a JSON configuration file.
- **Interactive CLI**: User-friendly command-line interface with rich formatting for easy interaction.
- **Diff Analysis**: Intelligent analysis of your staged changes to provide accurate commit message suggestions.

## Installation

```bash
pip install gitmuse
```

Note: GitMuse requires Python 3.11 or higher.

## Usage

1. Stage your changes as you normally would:

   ```bash
   git add .
   ```

2. Instead of using `git commit`, use GitMuse:

   ```bash
   gitmuse commit
   ```

3. GitMuse will analyze your changes and suggest a commit message. You can accept, modify, or reject the suggestion.

## Configuration

GitMuse can be configured to match your preferences. Create a `gitmuse.json` file in your project root or home directory:

```json
{
  "version": 1,
  "ai": {
    "provider": "ollama",
    "ollama": {
      "model": "llama3.1",
      "url": "http://localhost:11434",
      "max_tokens": 1000,
      "temperature": 0.7
    }
  },
  "commit": {
    "style": "conventional",
    "maxLength": 72,
    "includeScope": true,
    "includeBody": true,
    "includeFooter": true
  }
}
```

For more configuration options, refer to the `gitmuse-schema.json` file in the repository.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for more details.

## License

GitMuse is released under the MIT License. See the [LICENSE](LICENSE) file for more details.
