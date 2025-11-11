"""Example 2: Class Generation with Methods and Properties.

Demonstrates:
- Class generation with properties and methods
- Type-safe getters and setters
- Constructor with parameter validation

Usage:
    python examples/typescript/02-class-generation.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate a TypeScript class with full type safety."""
    print("Example 2: Class Generation")
    print("=" * 60)

    config = Config()
    config.project.language = "typescript"
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create a TypeScript class 'User' with:
    - Private properties: id (string), name (string), email (string)
    - Constructor that validates email format
    - Public getters for all properties
    - Method updateEmail(newEmail: string): void with validation
    - Method toJSON(): object"""

    print(f"\nGenerating User class...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅ Success' if result.success else '❌ Failed'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Class:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()


if __name__ == "__main__":
    main()
