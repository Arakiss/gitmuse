# GitMuse

GitMuse is an AI-powered tool that helps developers craft meaningful and descriptive Git commit messages. By analyzing your staged changes, GitMuse provides intelligent suggestions for your commit messages, making your Git history more informative and easier to navigate.

## Features

- **AI-Powered Commit Messages**: Leverages advanced AI models to generate context-aware commit messages.
- **Git Integration**: Seamlessly integrates with your existing Git workflow.
- **Customizable**: Adapt the AI suggestions to match your team's commit message style and conventions.
- **Interactive CLI**: User-friendly command-line interface for easy interaction.
- **Diff Analysis**: Intelligent analysis of your staged changes to provide accurate commit message suggestions.

## Installation

```bash
pip install gitmuse
```

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

GitMuse can be configured to match your preferences. Create a `.gitmuserc` file in your home directory:

```yaml
ai_model: gpt-4
commit_style: conventional
max_message_length: 72
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for more details.

## License

GitMuse is released under the MIT License. See the [LICENSE](LICENSE) file for more details.
