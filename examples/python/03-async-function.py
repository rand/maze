"""Example 3: Async Function with Error Handling.

Demonstrates:
- Async/await code generation
- Error handling with try/except
- Type hints for async functions

Usage:
    python examples/python/03-async-function.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate async Python function with error handling."""
    print("Python Example 3: Async Function Generation")
    print("=" * 60)

    config = Config()
    config.project.language = "python"
    config.constraints.syntactic_enabled = True
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create async Python function 'fetch_user_data':
    - Parameter: user_id: str
    - Returns: dict[str, Any]
    - Uses httpx for async HTTP requests (assume imported)
    - Handles exceptions with try/except
    - Returns None if user not found
    - Raises ValueError for invalid user_id format
    - Includes type hints and docstring"""

    print(f"\nGenerating async function...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Async Function:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    if result.validation:
        print(f"\nValidation:")
        print(f"  Syntax: {'✅' if result.validation.syntax_valid else '❌'}")
        print(f"  Errors: {result.validation.errors_found}")

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
