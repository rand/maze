"""Example 4: FastAPI Endpoint Generation.

Demonstrates:
- REST API endpoint generation for FastAPI
- Pydantic model integration
- Request/response type safety

Usage:
    python examples/python/04-fastapi-endpoint.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate FastAPI endpoint with Pydantic models."""
    print("Python Example 4: FastAPI Endpoint Generation")
    print("=" * 60)

    config = Config()
    config.project.language = "python"
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = """Create a FastAPI POST endpoint for user creation:
    - Endpoint: @app.post("/users", response_model=UserResponse)
    - Request model: UserCreate (Pydantic BaseModel)
      - name: str (min_length=1, max_length=100)
      - email: EmailStr
      - age: int | None (optional)
    - Response model: UserResponse (Pydantic BaseModel)
      - id: str
      - name: str
      - email: str
      - created_at: datetime
    - Function: async def create_user(user: UserCreate) -> UserResponse
    - Validate email format
    - Return 201 status
    - Include proper type hints and docstrings"""

    print(f"\nGenerating FastAPI endpoint...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated Endpoint:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
