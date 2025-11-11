"""Example 2: Go Struct with Methods.

Demonstrates:
- Struct definition
- Methods with pointer receivers
- Constructor pattern

Usage:
    python examples/go/02-struct-methods.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate Go struct with methods."""
    print("Go Example 2: Struct with Methods")
    print("=" * 60)

    config = Config()
    config.project.language = "go"
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create Go struct 'Counter' with methods:
    - Field: count int
    - New() *Counter - constructor
    - Increment() - pointer receiver, increments count
    - Value() int - value receiver, returns count
    - Reset() - pointer receiver, sets count to 0
    - Include documentation comments"""

    print(f"\nGenerating Counter struct...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅ Success' if result.success else '❌ Failed'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Code:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
