"""Example 1: Python Function Generation with Type Hints.

Demonstrates:
- Function generation with PEP 484 type hints
- Using Maze with Python projects
- Type-safe code generation

Usage:
    python examples/python/01-function-generation.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate a Python function with type hints."""
    print("Python Example 1: Function Generation with Type Hints")
    print("=" * 60)

    # Configure for Python
    config = Config()
    config.project.language = "python"
    config.project.name = "python-function-example"
    config.constraints.syntactic_enabled = True
    config.constraints.type_enabled = True

    # Create pipeline
    pipeline = Pipeline(config)

    # Generate function
    prompt = """Create a Python function called 'calculate_bmi' that:
    - Takes weight (float) in kg and height (float) in meters
    - Returns BMI (float) rounded to 1 decimal place
    - Validates inputs (weight > 0, height > 0)
    - Raises ValueError for invalid inputs
    - Includes docstring"""

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

    # Show validation
    if result.validation:
        print(f"\nValidation:")
        print(f"  Syntax Valid: {result.validation.syntax_valid}")
        print(f"  Errors: {result.validation.errors_found}")

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
