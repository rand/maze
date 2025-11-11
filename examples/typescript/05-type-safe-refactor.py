"""Example 5: Type-Safe Code Refactoring.

Demonstrates:
- Refactoring existing code with type constraints
- Preserving type safety during transformation
- Using project context for conventions

Usage:
    python examples/typescript/05-type-safe-refactor.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline
from maze.core.types import TypeContext


def main():
    """Refactor code while maintaining type safety."""
    print("Example 5: Type-Safe Refactoring")
    print("=" * 60)

    config = Config()
    config.project.language = "typescript"
    config.constraints.type_enabled = True
    config.constraints.contextual_enabled = True

    pipeline = Pipeline(config)

    # Original code to refactor
    original_code = """
function processUsers(users) {
    return users.map(u => ({
        fullName: u.firstName + ' ' + u.lastName,
        age: u.age,
        isAdult: u.age >= 18
    }));
}
"""

    print("Original Code:")
    print("-" * 60)
    print(original_code)
    print("-" * 60)

    prompt = f"""Refactor this function to be type-safe:
{original_code}

Add:
- Proper TypeScript types for User input
- Type for the returned transformed objects
- Make it a generic function if appropriate
- Keep the same logic"""

    print(f"\nRefactoring to add types...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nRefactored Code:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()


if __name__ == "__main__":
    main()
