"""Example 1: Zig Function Generation.

Usage:
    python examples/zig/01-function.py
"""

from maze.config import Config
from maze.core.pipeline import Pipeline

def main():
    print("Zig Example 1: Function Generation")
    print("=" * 60)
    
    config = Config()
    config.project.language = "zig"
    pipeline = Pipeline(config)
    
    result = pipeline.run("Create Zig function to add two i32 numbers")
    
    print(f"Status: {'✅' if result.success else '❌'}")
    print(f"\nGenerated Code:\n{'-'*60}\n{result.code}\n{'-'*60}")
    pipeline.close()
    print("\n✅ Example complete!")

if __name__ == "__main__":
    main()
