"""Integration Example 2: CI/CD Pipeline Integration.

Demonstrates:
- Using Maze in CI/CD workflows
- Automated code generation for boilerplate
- Validation in build pipeline

This is a conceptual example showing integration patterns.

Usage:
    python examples/integration/02-ci-pipeline.py
"""

from pathlib import Path

from maze.config import Config
from maze.core.pipeline import Pipeline


def generate_boilerplate(spec_file: Path) -> dict:
    """Generate boilerplate code from specification.

    Args:
        spec_file: Path to specification file

    Returns:
        Dictionary with generated files
    """
    config = Config()
    config.project.language = "typescript"
    
    pipeline = Pipeline(config)
    
    # Simulate reading spec
    spec = {
        "models": ["User", "Task", "Project"],
        "crud_operations": True,
        "validation": True,
    }
    
    generated_files = {}
    
    # Generate model for each entity
    for model in spec["models"]:
        prompt = f"""Generate TypeScript interface and class for {model} model with:
        - Interface {model}Data with id, createdAt, updatedAt
        - Class {model} implementing the interface
        - CRUD methods if enabled
        - Validation methods if enabled"""
        
        result = pipeline.run(prompt)
        
        if result.success:
            generated_files[f"{model.lower()}.ts"] = result.code
    
    pipeline.close()
    return generated_files


def main():
    """Demonstrate CI/CD integration."""
    print("Integration Example 2: CI/CD Pipeline")
    print("=" * 60)

    spec_file = Path("spec.json")
    
    print("\nGenerating boilerplate from specification...\n")

    generated = generate_boilerplate(spec_file)

    print(f"Generated {len(generated)} files:")
    for filename in generated.keys():
        print(f"  - {filename}")

    print("\n✅ Example complete!")
    print("\nCI/CD Integration Pattern:")
    print("  1. Trigger on spec file changes")
    print("  2. Run Maze generation")
    print("  3. Validate generated code")
    print("  4. Commit and push if valid")
    print("  5. Create PR for review")
    
    print("\nSample GitHub Actions workflow:")
    print("""
    name: Generate Boilerplate
    on:
      push:
        paths: ['spec/**']
    jobs:
      generate:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - name: Setup Maze
            run: pip install maze
          - name: Generate code
            run: maze generate --from-spec spec.json
          - name: Validate
            run: maze validate generated/**/*.ts
          - name: Create PR
            if: success()
            run: gh pr create --title "Generated code"
    """)


if __name__ == "__main__":
    main()
