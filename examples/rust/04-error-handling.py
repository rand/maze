"""Example 4: Custom Error Type with thiserror.

Demonstrates:
- Custom error enum
- Error trait implementation
- Using thiserror derive

Usage:
    python examples/rust/04-error-handling.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate Rust custom error type."""
    print("Rust Example 4: Custom Error Type")
    print("=" * 60)

    config = Config()
    config.project.language = "rust"
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create Rust error enum using thiserror:
    - Name: AppError
    - Variants: NotFound(String), Invalid(String), Internal
    - Use #[derive(Error, Debug)]
    - Use #[error("...")] for display messages
    - Implement From<std::io::Error> for AppError
    - Include documentation"""

    print(f"\nGenerating custom error type...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Error Type:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
