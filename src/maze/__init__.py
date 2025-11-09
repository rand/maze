"""
MAZE: Adaptive Constrained Code Generation System

A production-ready adaptive constraint-based code generation system
that combines LLM capabilities with formal constraint enforcement.
"""

__version__ = "0.1.0"

# Note: These imports will be uncommented as modules are created
# from maze.api import (
#     MazeGenerator,
#     AsyncMazeGenerator,
#     Specification,
#     GenerationResult,
#     ValidationResult,
# )
#
# from maze.core import (
#     Type,
#     TypeContext,
#     Constraint,
#     ConstraintLevel,
#     ConstraintSet,
#     IndexedContext,
# )

__all__ = [
    "__version__",
]

def main() -> None:
    """Main entry point for the maze CLI."""
    print(f"Maze v{__version__} - Adaptive Constrained Code Generation System")
    print("Use 'maze --help' for usage information.")