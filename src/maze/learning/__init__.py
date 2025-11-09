"""
Learning module for adaptive constraint-based code generation.

Provides pattern mining, constraint learning, and project adaptation.
"""

from maze.learning.pattern_mining import (
    PatternMiningEngine,
    SyntacticPattern,
    TypePattern,
    SemanticPattern,
    PatternSet
)
from maze.learning.constraint_learning import (
    ConstraintLearningSystem,
    ConstraintRefinement,
    Feedback,
    GenerationResult,
    ValidationResult,
    RepairResult,
    LearningEvent,
)
from maze.learning.project_adaptation import (
    ProjectAdaptationManager,
    ProjectProfile,
    ConventionSet,
    AdaptationStats,
)
from maze.learning.feedback_orchestrator import (
    FeedbackLoopOrchestrator,
    FeedbackResult,
    FeedbackStats,
)
from maze.learning.hybrid_weighting import (
    HybridConstraintWeighter,
    WeightedConstraintSet,
    TokenWeights,
    ConstraintSet,
    GenerationState,
)

__all__ = [
    # Pattern mining
    "PatternMiningEngine",
    "SyntacticPattern",
    "TypePattern",
    "SemanticPattern",
    "PatternSet",
    # Constraint learning
    "ConstraintLearningSystem",
    "ConstraintRefinement",
    "Feedback",
    "GenerationResult",
    "ValidationResult",
    "RepairResult",
    "LearningEvent",
    # Project adaptation
    "ProjectAdaptationManager",
    "ProjectProfile",
    "ConventionSet",
    "AdaptationStats",
    # Feedback orchestration
    "FeedbackLoopOrchestrator",
    "FeedbackResult",
    "FeedbackStats",
    # Hybrid weighting
    "HybridConstraintWeighter",
    "WeightedConstraintSet",
    "TokenWeights",
    "ConstraintSet",
    "GenerationState",
]
