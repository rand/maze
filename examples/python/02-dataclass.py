"""Example 2: Dataclass Generation with Validation.

Demonstrates:
- Dataclass generation with type hints
- Field validation
- Custom methods

Usage:
    python examples/python/02-dataclass.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate a Python dataclass with validation."""
    print("Python Example 2: Dataclass Generation")
    print("=" * 60)

    config = Config()
    config.project.language = "python"
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create a Python dataclass 'Product' with:
    - id: str (UUID)
    - name: str (not empty)
    - price: float (positive)
    - quantity: int (non-negative, default 0)
    - tags: list[str] (default empty list)
    - Use @dataclass decorator
    - Add __post_init__ for validation
    - Add method to_dict() -> dict[str, Any]
    - Include docstrings"""

    print(f"\nGenerating Product dataclass...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅ Success' if result.success else '❌ Failed'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Dataclass:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
