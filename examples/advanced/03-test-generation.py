"""Advanced Example 3: Test Generation Matching Project Conventions.

Demonstrates:
- Generating tests that match project patterns
- Using project context for test style
- Creating comprehensive test coverage

Usage:
    python examples/advanced/03-test-generation.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate tests matching project conventions."""
    print("Advanced Example 3: Test Generation")
    print("=" * 60)

    # Source code to test
    source_code = """
export class Calculator {
    add(a: number, b: number): number {
        return a + b;
    }

    subtract(a: number, b: number): number {
        return a - b;
    }

    divide(a: number, b: number): number {
        if (b === 0) {
            throw new Error('Division by zero');
        }
        return a / b;
    }
}
"""

    print("Source Code to Test:")
    print("-" * 60)
    print(source_code)
    print("-" * 60)

    config = Config()
    config.project.language = "typescript"
    config.constraints.contextual_enabled = True

    pipeline = Pipeline(config)

    prompt = f"""Generate comprehensive tests for this Calculator class:

{source_code}

Requirements:
- Use Jest or Vitest framework
- Test all methods
- Include edge cases (division by zero, negative numbers)
- Use describe/it blocks
- Add type assertions
- Follow TypeScript testing best practices"""

    print("\nGenerating tests...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Tests:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()


if __name__ == "__main__":
    main()
