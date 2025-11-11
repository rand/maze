"""Example 1: Function Generation with Type Constraints.

Demonstrates:
- Basic function generation with type signatures
- Using Maze pipeline programmatically
- Validation and metrics collection

Usage:
    python examples/typescript/01-function-generation.py
"""

from pathlib import Path

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate a TypeScript function with type constraints."""
    print("Example 1: Function Generation with Type Constraints")
    print("=" * 60)

    # Configure Maze
    config = Config()
    config.project.language = "typescript"
    config.project.name = "function-example"
    config.constraints.syntactic_enabled = True
    config.constraints.type_enabled = True

    # Create pipeline
    pipeline = Pipeline(config)

    # Generate function
    prompt = """Create a TypeScript function called 'calculateDiscount' that:
    - Takes price (number) and discount percentage (number)
    - Returns the discounted price (number)
    - Validates inputs (price > 0, discount between 0-100)
    - Throws error for invalid inputs"""

    print(f"\nPrompt: {prompt}\n")
    print("Generating...")

    result = pipeline.run(prompt)

    print(f"\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.total_duration_ms:.0f}ms")

    if result.generation:
        print(f"  Tokens: {result.generation.tokens_generated}")

    print(f"\nGenerated Code:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    # Show metrics
    if result.validation:
        print(f"\nValidation:")
        print(f"  Syntax Valid: {result.validation.syntax_valid}")
        print(f"  Type Valid: {result.validation.type_valid}")
        print(f"  Errors: {result.validation.errors_found}")

    # Get metrics summary
    metrics = pipeline.metrics.summary()
    if "latencies" in metrics and metrics["latencies"]:
        print(f"\nPerformance Metrics:")
        for op, stats in metrics["latencies"].items():
            if stats:
                print(f"  {op}: {stats['mean']:.2f}ms")

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
