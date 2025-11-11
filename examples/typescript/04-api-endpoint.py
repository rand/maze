"""Example 4: REST API Endpoint Generation.

Demonstrates:
- Express.js API endpoint generation
- Request/response type definitions
- Error handling with proper HTTP codes
- Input validation

Usage:
    python examples/typescript/04-api-endpoint.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate a REST API endpoint with full type safety."""
    print("Example 4: API Endpoint Generation")
    print("=" * 60)

    config = Config()
    config.project.language = "typescript"
    config.constraints.syntactic_enabled = True
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create an Express.js API endpoint handler for user creation:
    - POST /api/users
    - Request body type: { name: string, email: string, age?: number }
    - Response type: { id: string, name: string, email: string, createdAt: Date }
    - Validate email format
    - Return 400 for invalid input
    - Return 201 with created user
    - Include async/await error handling"""

    print(f"\nGenerating API endpoint...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Endpoint:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    if result.validation:
        print(f"\nValidation Results:")
        print(f"  Syntax: {'✅' if result.validation.syntax_valid else '❌'}")
        print(f"  Types: {'✅' if result.validation.type_valid else '❌'}")

    pipeline.close()


if __name__ == "__main__":
    main()
