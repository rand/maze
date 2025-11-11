"""Example 3: Async Function with Tokio.

Demonstrates:
- Async/await in Rust
- Error handling with Result
- External crate usage (tokio, reqwest)

Usage:
    python examples/rust/03-async-tokio.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate async Rust function with tokio."""
    print("Rust Example 3: Async Function with Tokio")
    print("=" * 60)

    config = Config()
    config.project.language = "rust"
    config.constraints.syntactic_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create async Rust function 'fetch_user':
    - Parameter: user_id: &str
    - Returns: Result<User, reqwest::Error>
    - Use reqwest to fetch from API
    - Async function with .await
    - Error handling with ?
    - Assume User struct exists
    - Include documentation"""

    print(f"\nGenerating async function...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Async Function:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
