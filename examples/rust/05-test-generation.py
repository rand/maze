"""Example 5: Rust Test Generation.

Demonstrates:
- Test function generation
- #[test] attributes
- #[cfg(test)] modules
- Assert macros

Usage:
    python examples/rust/05-test-generation.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate Rust tests."""
    print("Rust Example 5: Test Generation")
    print("=" * 60)

    # Source code to test
    source_code = """
pub struct Calculator;

impl Calculator {
    pub fn add(&self, a: i32, b: i32) -> i32 {
        a + b
    }
    
    pub fn subtract(&self, a: i32, b: i32) -> i32 {
        a - b
    }
}
"""

    print("Source Code to Test:")
    print("-" * 60)
    print(source_code)
    print("-" * 60)

    config = Config()
    config.project.language = "rust"

    pipeline = Pipeline(config)

    prompt = f"""Generate Rust tests for this Calculator:

{source_code}

Requirements:
- Use #[cfg(test)] module
- Use #[test] attribute
- Test add() method
- Test subtract() method
- Test edge cases (zero, negative numbers)
- Use assert_eq! macro
- Include module documentation"""

    print("\nGenerating Rust tests...\n")

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
