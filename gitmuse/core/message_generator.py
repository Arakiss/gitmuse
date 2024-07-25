import os
from gitmuse.core.diff_analyzer import analyze_diff
from gitmuse.config.settings import COMMIT_KEYWORDS


def generate_commit_message(diff: str) -> str:
    changes = analyze_diff(diff)

    files_changed = list(
        set(change["file"] for category in changes.values() for change in category)
    )
    files_summary = ", ".join(files_changed[:3]) + (
        "..." if len(files_changed) > 3 else ""
    )
    changes_summary = ", ".join(
        f"{category.capitalize()}: {len(items)} file(s)"
        for category, items in changes.items()
        if items
    )

    detailed_changes = []
    for category, items in changes.items():
        for item in items:
            file_ext = os.path.splitext(item["file"])[1]
            if file_ext == ".md":
                detailed_changes.append(
                    f"{category.capitalize()} documentation: {item['file']}"
                )
            elif file_ext in [".py", ".js", ".ts"]:
                detailed_changes.append(
                    f"{category.capitalize()} code in {item['file']}"
                )
            else:
                detailed_changes.append(f"{category.capitalize()} {item['file']}")

    prompt = f"""
    Generate a git commit message for the following changes:
    Files changed: {files_summary}
    Summary: {changes_summary}

    Detailed changes:
    {' '.join(detailed_changes)}

    Follow these guidelines:
    1. Start with an emoji and an imperative present active verb from this list: {', '.join([f'{emoji} {verb}' for verb, emoji in COMMIT_KEYWORDS.items()])}
    2. The first line should be a summary, maximum 50 characters (including the emoji)
    3. Leave a blank line after the summary
    4. Provide a more detailed description of the changes
    5. Use bullet points for multiple changes
    6. Be specific and clear about what changed and why
    7. Don't include the full file names in the message body

    Format the message like this:
    🎨 Verb Summary of changes

    - Detailed explanation of changes
    - Another point if necessary

    IMPORTANT: Provide ONLY the commit message, no additional explanations.
    """

    return prompt
