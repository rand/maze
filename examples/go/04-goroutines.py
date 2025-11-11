"""Example 4: Goroutines and Channels.

Demonstrates:
- Goroutine spawning
- Channel communication
- Select statement
- Concurrency patterns

Usage:
    python examples/go/04-goroutines.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate Go code with goroutines and channels."""
    print("Go Example 4: Goroutines and Channels")
    print("=" * 60)

    config = Config()
    config.project.language = "go"

    pipeline = Pipeline(config)

    prompt = """Create Go function 'ProcessConcurrently':
    - Parameter: items []string
    - Returns: []string
    - Process each item in a goroutine
    - Use channels to collect results
    - Use sync.WaitGroup or channel coordination
    - Return processed results
    - Include documentation"""

    print(f"\nGenerating concurrent processing...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Code:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
