"""Example 3: Go Interface and Implementation.

Demonstrates:
- Interface definition
- Implicit interface implementation
- Polymorphism

Usage:
    python examples/go/03-interface.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate Go interface and implementation."""
    print("Go Example 3: Interface and Implementation")
    print("=" * 60)

    config = Config()
    config.project.language = "go"

    pipeline = Pipeline(config)

    prompt = """Create Go Repository interface and implementation:
    - Interface Repository with:
      - Find(id string) (*User, error)
      - Save(user *User) error
      - Delete(id string) error
    - Struct InMemoryRepo implementing Repository
    - Use map[string]*User for storage
    - Include documentation"""

    print(f"\nGenerating Repository interface...\n")

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
