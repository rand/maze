"""Example 2: Rust Struct with Trait Implementation.

Demonstrates:
- Struct definition
- Trait implementation
- Method generation

Usage:
    python examples/rust/02-struct-trait.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate Rust struct with trait implementation."""
    print("Rust Example 2: Struct with Trait Implementation")
    print("=" * 60)

    config = Config()
    config.project.language = "rust"
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create Rust struct 'Point' and implement Display:
    - Struct Point with x: f64, y: f64 fields
    - Implement std::fmt::Display trait
    - Format as "(x, y)"
    - Add impl block with new() constructor
    - Include documentation comments"""

    print(f"\nGenerating Point struct with Display...\n")

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
