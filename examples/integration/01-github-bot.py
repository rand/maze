"""Integration Example 1: GitHub Code Review Bot.

Demonstrates:
- Using Maze in GitHub Actions workflow
- Automated code suggestions
- CI/CD integration

This is a conceptual example showing integration patterns.

Usage:
    python examples/integration/01-github-bot.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def review_pull_request(pr_files: list[str]) -> dict:
    """Review pull request files and generate suggestions.

    Args:
        pr_files: List of file paths in PR

    Returns:
        Dictionary with review comments
    """
    config = Config()
    config.project.language = "typescript"
    
    pipeline = Pipeline(config)
    
    suggestions = {}
    
    for file_path in pr_files:
        # Read file content (simulated)
        code = f"// Content of {file_path}"
        
        # Validate code
        validation = pipeline.validate(code)
        
        if not validation.success:
            suggestions[file_path] = [
                {
                    "line": diag.line,
                    "message": diag.message,
                    "suggestion": diag.suggested_fix,
                }
                for diag in validation.diagnostics[:5]
            ]
    
    pipeline.close()
    return suggestions


def main():
    """Demonstrate GitHub bot integration."""
    print("Integration Example 1: GitHub Code Review Bot")
    print("=" * 60)

    # Simulate PR files
    pr_files = [
        "src/api/users.ts",
        "src/api/tasks.ts",
        "src/utils/validation.ts",
    ]

    print(f"\nReviewing {len(pr_files)} files from PR...\n")

    suggestions = review_pull_request(pr_files)

    print(f"Review Complete!")
    print(f"Files with suggestions: {len(suggestions)}")

    for file_path, comments in suggestions.items():
        print(f"\n{file_path}:")
        for comment in comments:
            print(f"  Line {comment['line']}: {comment['message']}")

    print("\n✅ Example complete!")
    print("\nIntegration Pattern:")
    print("  1. Trigger on PR events (GitHub Actions)")
    print("  2. Read changed files")
    print("  3. Run Maze validation")
    print("  4. Post comments on PR")


if __name__ == "__main__":
    main()
