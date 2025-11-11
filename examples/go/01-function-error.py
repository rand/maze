"""Example 1: Go Function with Error Return.

Demonstrates:
- Function with error return (Go idiom)
- Error handling
- Type safety

Usage:
    python examples/go/01-function-error.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate Go function with error return."""
    print("Go Example 1: Function with Error Return")
    print("=" * 60)

    config = Config()
    config.project.language = "go"
    config.constraints.syntactic_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create a Go function called 'Divide':
    - Parameters: a float64, b float64
    - Returns: (float64, error)
    - Return error if b == 0
    - Return result and nil otherwise
    - Include documentation comment"""

    print(f"\nPrompt: {prompt}\n")
    print("Generating...")

    result = pipeline.run(prompt)

    print(f"\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Code:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
