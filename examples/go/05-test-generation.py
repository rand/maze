"""Example 5: Go Test Generation.

Demonstrates:
- Test function generation
- Table-driven tests
- testing package usage

Usage:
    python examples/go/05-test-generation.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate Go tests."""
    print("Go Example 5: Test Generation")
    print("=" * 60)

    # Source code to test
    source_code = """
package calculator

func Add(a, b int) int {
    return a + b
}

func Subtract(a, b int) int {
    return a - b
}
"""

    print("Source Code to Test:")
    print("-" * 60)
    print(source_code)
    print("-" * 60)

    config = Config()
    config.project.language = "go"

    pipeline = Pipeline(config)

    prompt = f"""Generate Go tests for this calculator package:

{source_code}

Requirements:
- Use testing package
- Test Add() function
- Test Subtract() function
- Use table-driven tests
- Include edge cases (zero, negative)
- Function names: TestAdd, TestSubtract
- Include documentation comments"""

    print("\nGenerating Go tests...\n")

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
