"""Advanced Example 1: Full REST API Generation with OpenAPI Schema.

Demonstrates:
- Generating complete REST API from OpenAPI schema
- Type generation from JSON Schema
- Multiple endpoint generation
- Request/response validation

Usage:
    python examples/advanced/01-api-generation.py
"""

import json
from pathlib import Path

from maze.config import Config
from maze.core.pipeline import Pipeline


def main():
    """Generate REST API from OpenAPI schema."""
    print("Advanced Example 1: API Generation from OpenAPI")
    print("=" * 60)

    # Sample OpenAPI schema
    openapi_schema = {
        "openapi": "3.0.0",
        "info": {"title": "Task API", "version": "1.0.0"},
        "paths": {
            "/tasks": {
                "get": {
                    "summary": "List all tasks",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Task"},
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "summary": "Create task",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CreateTask"}
                            }
                        },
                    },
                },
            }
        },
        "components": {
            "schemas": {
                "Task": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "completed": {"type": "boolean"},
                    },
                },
                "CreateTask": {
                    "type": "object",
                    "required": ["title"],
                    "properties": {"title": {"type": "string"}},
                },
            }
        },
    }

    config = Config()
    config.project.language = "typescript"
    config.constraints.type_enabled = True

    pipeline = Pipeline(config)

    prompt = f"""Generate Express.js API endpoints from this OpenAPI schema:

{json.dumps(openapi_schema, indent=2)}

Generate:
1. TypeScript interfaces for Task and CreateTask
2. GET /tasks endpoint handler
3. POST /tasks endpoint handler
4. Input validation
5. Proper error handling"""

    print("\nGenerating API from schema...\n")

    result = pipeline.run(prompt)

    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")

    print(f"\nGenerated API Code:")
    print("-" * 60)
    print(result.code)
    print("-" * 60)

    # Show metrics
    summary = pipeline.metrics.summary()
    if summary.get("latencies"):
        print(f"\nPerformance:")
        for op, stats in summary["latencies"].items():
            if stats:
                print(f"  {op}: {stats['mean']:.0f}ms")

    pipeline.close()
    print("\n✅ Example complete!")


if __name__ == "__main__":
    main()
