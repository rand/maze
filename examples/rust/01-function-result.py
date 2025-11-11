"""Example 1: Rust Function with Result Type.

Demonstrates:
- Function generation with Result type
- Error handling patterns
- Type safety with Rust

Usage:
    python examples/rust/01-function-result.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate Rust function with Result type."""
    print("Rust Example 1: Function with Result Type")
    print("=" * 60)

    config = Config()
    config.project.language = "rust"
    config.constraints.syntactic_enabled = True
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create a Rust function called 'divide':
    - Parameters: a: f64, b: f64
    - Returns: Result<f64, String>
    - Returns Err if b is 0.0
    - Returns Ok(a / b) otherwise
    - Include error message in Err
    - Add documentation comment"""

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

    if result.validation:
        print(f"\nValidation:")
        print(f"  Syntax Valid: {result.validation.syntax_valid}")
        print(f"  Errors: {result.validation.errors_found}")

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
