"""Example 5: Pytest Test Generation.

Demonstrates:
- Test generation matching pytest conventions
- Comprehensive test coverage
- Fixture usage

Usage:
    python examples/python/05-test-generation.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate pytest tests for a Python class."""
    print("Python Example 5: Pytest Test Generation")
    print("=" * 60)

    # Source code to test
    source_code = """
class StringProcessor:
    def reverse(self, text: str) -> str:
        return text[::-1]
    
    def uppercase(self, text: str) -> str:
        return text.upper()
    
    def word_count(self, text: str) -> int:
        return len(text.split())
"""

    print("Source Code to Test:")
    print("-" * 60)
    print(source_code)
    print("-" * 60)

    config = Config()
    config.project.language = "python"
    config.constraints.contextual_enabled = True

    pipeline = Pipeline(config)

    prompt = f"""Generate comprehensive pytest tests for this StringProcessor class:

{source_code}

Requirements:
- Use pytest framework
- Test all methods (reverse, uppercase, word_count)
- Include edge cases (empty string, special characters)
- Use pytest fixtures if helpful
- Follow naming convention: test_<method>_<scenario>
- Add type hints to test functions
- Use assert statements
- Include docstrings"""

    print("\nGenerating pytest tests...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Tests:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
