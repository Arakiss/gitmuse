# GitMuse

GitMuse is an AI-powered tool that helps developers craft meaningful and descriptive Git commit messages. By analyzing your staged changes, GitMuse provides intelligent suggestions for your commit messages, making your Git history more informative and easier to navigate.

[![Release](https://github.com/Arakiss/gitmuse/actions/workflows/release.yml/badge.svg?branch=main&event=status)](https://github.com/Arakiss/gitmuse/actions/workflows/release.yml)

## Key Features

- **No Configuration Needed**: Works out-of-the-box with Llama 3.2 and Ollama.
- **AI-Powered Commit Messages**: Leverages OpenAI's GPT models, or Ollama for locally hosted models, to generate context-aware commit messages.
- **Git Integration**: Seamlessly integrates with your existing Git workflow.
- **Customizable**: Configure AI providers, commit message styles, and other preferences via a JSON configuration file.
- **Interactive CLI**: User-friendly command-line interface with rich formatting for easy interaction.
- **Diff Analysis**: Intelligent analysis of your staged changes to provide accurate commit message suggestions.

## Installation

```bash
pip install gitmuse
```

**Note**: GitMuse requires Python 3.11 or higher and Ollama installed with the Llama 3.2 model downloaded for zero configuration.

## Usage

1. Ensure that Ollama is running:

   ```bash
   ollama serve
   ```

2. Stage your changes as you normally would:

   ```bash
   git add .
   ```

3. Instead of using `git commit`, use GitMuse:

   ```bash
   gitmuse commit
   ```

4. GitMuse will analyze your changes and suggest a commit message.
5. You can view the diff, edit the commit message, and confirm or cancel the commit.
6. If confirmed, GitMuse will create the commit with the generated or edited message.

## Development Status

GitMuse is currently in active development and is fully functional with Llama 3.2 by default, requiring no additional configuration as long as Ollama is installed and the model is downloaded. It also works with OpenAI and any of their models by default. The project now includes improved error handling, logging, and a more interactive CLI experience.

## Configuration (Optional)

GitMuse can be configured to match your preferences. You can create a `gitmuse.json` file in one of the following locations (in order of precedence):

1. In your current project directory
2. In your home directory: `~/.config/gitmuse/gitmuse.json`
3. In the global configuration directory: `/etc/gitmuse/gitmuse.json`

The configuration file should follow this structure:

```json
{
  "version": 1,
  "ai": {
    "provider": "ollama",
    "openai": {
      "model": "gpt-4",
      "apiKey": "YOUR_API_KEY_HERE",
      "organizationId": "YOUR_ORG_ID_HERE",
      "max_tokens": 1000,
      "temperature": 0.7
    },
    "ollama": {
      "model": "llama3.2",
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
    "includeFooter": true,
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
      "chore": "🧹"
    }
  },
  "prompts": {
    "commitMessage": {
      "useDefault": true,
      "customTemplate": ""
    }
  },
  "logging": {
    "level": "INFO",
    "format": "console",
    "file": ""
  }
}
```

For more configuration options, refer to the `gitmuse-schema.json` file in the repository.

## Roadmap

- **Support for Additional AI Providers**:
  - Groq
  - AWS Bedrock
  - Azure OpenAI Service

## FAQ

### Why does GitMuse work by default with Ollama and Llama 3.2?

Llama 3.2 from Meta is one of the most advanced open-source language models available, offering high precision, support for function calling, and multilingual capabilities. It's an excellent default choice for generating high-quality, context-aware commit messages, excelling in various tasks including general knowledge, multilingual translation, and contextual understanding.

### What should I do if I encounter issues during installation?

1. **Upgrade pip**:

   ```bash
   python -m pip install --upgrade pip
   ```

2. **Check Python version**: Ensure you are using Python 3.11 or higher:

   ```bash
   python --version
   ```

### GitMuse is installed but the `gitmuse` command is not found. What should I do?

1. **Check PATH**: Ensure that your Python `bin` directory is in your system's PATH. Add it to your PATH by modifying your shell configuration file (e.g., `.bashrc`, `.zshrc`):

   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Reinstall GitMuse**: Sometimes reinstalling the package can resolve PATH issues:

   ```bash
   pip uninstall gitmuse
   pip install gitmuse
   ```

### GitMuse is not generating commit messages as expected. What can I do?

1. **Check configuration**: Ensure your `gitmuse.json` configuration file is correctly set up if you have one.

2. **Update GitMuse**: Make sure you have the latest version of GitMuse:

   ```bash
   pip install --upgrade gitmuse
   ```

3. **Review error messages**: If there are error messages, review them for clues about what might be wrong. Ensure all dependencies are correctly installed.

4. **Check Ollama**: If using Ollama, make sure it's running and the Llama 3.2 model is properly installed.

5. **Logging**: Check the logs for more detailed information about any issues. You can adjust the logging level in the configuration file for more verbose output.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for more details.

## Support

For support, visit our [GitHub Issues](https://github.com/Arakiss/gitmuse/issues).
