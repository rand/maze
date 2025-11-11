"""Example 3: Interface and Type Definition Generation.

Demonstrates:
- Interface generation with generic types
- Type aliases and unions
- Complex type composition

Usage:
    python examples/typescript/03-interface-generation.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate TypeScript interfaces with generics."""
    print("Example 3: Interface Generation")
    print("=" * 60)

    config = Config()
    config.project.language = "typescript"
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create TypeScript type definitions for a repository pattern:
    - Interface Repository<T> with methods:
      - findById(id: string): Promise<T | null>
      - findAll(): Promise<T[]>
      - save(entity: T): Promise<T>
      - delete(id: string): Promise<boolean>
    - Type alias QueryOptions with properties:
      - limit?: number
      - offset?: number
      - sortBy?: string
      - sortOrder?: 'asc' | 'desc'"""

    print(f"\nGenerating repository interfaces...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Interfaces:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()


if __name__ == "__main__":
    main()
