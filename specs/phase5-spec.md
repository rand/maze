# Phase 5: Adaptive Learning - Specification

## Overview

Implement pattern mining, constraint learning, and project-specific adaptation to enable Maze to improve with usage and adapt to project conventions. This phase integrates with mnemosyne for persistent cross-session learning.

## Goals

1. **Improvement**: >10% quality improvement with learning enabled
2. **Adaptation Speed**: <100 examples for project convergence
3. **Pattern Recall**: >90% cross-session pattern retention
4. **Performance**: <50ms pattern lookup, <10% generation overhead
5. **Integration**: Full mnemosyne orchestration for agentic workflows

## Components

### 1. Pattern Mining Engine

**Purpose**: Extract reusable patterns from existing codebases

**Key Features**:
- Multi-level pattern extraction (syntax, structure, idioms)
- Frequency analysis and ranking
- Context-aware pattern matching
- Language-specific extractors
- Incremental mining for large codebases

**Patterns to Extract**:
- **Syntactic**: Common code structures, naming conventions
- **Type**: Recurring type signatures, generic patterns
- **Semantic**: Function composition patterns, error handling
- **Style**: Code formatting, comment patterns, documentation style

**Interface**:
```python
class PatternMiningEngine:
    def mine_patterns(self, codebase: Path, language: str) -> PatternSet
    def extract_syntactic_patterns(self, ast: AST) -> list[SyntacticPattern]
    def extract_type_patterns(self, types: TypeContext) -> list[TypePattern]
    def extract_semantic_patterns(self, code: str) -> list[SemanticPattern]
    def rank_patterns(self, patterns: list[Pattern]) -> list[ScoredPattern]
```

**Performance Target**: <5s for 100K LOC codebase

### 2. Constraint Learning System

**Purpose**: Learn soft constraints from patterns and generation feedback

**Learning Sources**:
- Successful generations (from repair loop)
- Accepted code (from validation pipeline)
- Project patterns (from pattern mining)
- User feedback (explicit or implicit)

**Constraint Types**:
- **Soft Syntactic**: Preferred structures (not enforced)
- **Type Preferences**: Common type choices for ambiguous situations
- **Semantic Patterns**: Typical implementation strategies
- **Style Rules**: Project-specific conventions

**Learning Algorithm**:
1. Observe successful generation + validation
2. Extract key features (pattern used, constraints applied)
3. Update weight for pattern in constraint set
4. Prune low-scoring patterns periodically

**Interface**:
```python
class ConstraintLearningSystem:
    def learn_from_success(
        self,
        generation_result: GenerationResult,
        validation_result: ValidationResult
    ) -> ConstraintRefinement

    def learn_from_failure(
        self,
        generation_result: GenerationResult,
        diagnostics: list[Diagnostic]
    ) -> ConstraintRefinement

    def update_weights(
        self,
        pattern: Pattern,
        feedback: Feedback
    ) -> float

    def prune_constraints(
        self,
        min_score: float = 0.1
    ) -> int
```

**Performance Target**: <10ms per learning update

### 3. Project Adaptation Manager

**Purpose**: Adapt Maze to project-specific conventions and patterns

**Adaptation Levels**:
- **Global**: Cross-project patterns (general best practices)
- **Project**: Project-specific conventions
- **Module**: Module-level patterns
- **File**: File-specific context

**Adaptation Process**:
1. Initial scan: Mine patterns from existing code
2. Bootstrap: Create initial constraint set
3. Refinement: Update based on generation feedback
4. Convergence: Stabilize after N examples

**Features**:
- Automatic project detection (package.json, pyproject.toml, etc.)
- Convention extraction (naming, structure, testing)
- Style guide inference
- API usage patterns
- Error handling conventions

**Interface**:
```python
class ProjectAdaptationManager:
    def initialize_project(self, project_path: Path) -> ProjectProfile
    def extract_conventions(self, project: ProjectProfile) -> ConventionSet
    def create_adapted_constraints(
        self,
        conventions: ConventionSet
    ) -> ConstraintSet

    def update_from_feedback(
        self,
        feedback: GenerationFeedback
    ) -> None

    def get_adaptation_stats(self) -> AdaptationStats
```

**Performance Target**: <30s initial project scan

### 4. Feedback Loop Orchestrator

**Purpose**: Coordinate learning from generation results

**Feedback Sources**:
- Validation pipeline results
- Repair iteration outcomes
- Test execution results
- Security review findings
- User acceptance/rejection

**Feedback Processing**:
1. Collect feedback from all sources
2. Classify feedback type (positive/negative, source)
3. Update pattern scores
4. Adjust constraint weights
5. Persist learned patterns to mnemosyne

**Weighted Scoring**:
- Test pass: +2.0
- Validation success: +1.0
- Repair in 1 attempt: +1.5
- Repair in >1 attempt: +0.5
- Security violation: -3.0
- Validation failure: -1.0

**Interface**:
```python
class FeedbackLoopOrchestrator:
    def __init__(
        self,
        learner: ConstraintLearningSystem,
        adapter: ProjectAdaptationManager,
        memory: MnemosyneIntegration
    ):
        ...

    def process_feedback(
        self,
        generation: GenerationResult,
        validation: ValidationResult,
        repair: Optional[RepairResult] = None
    ) -> FeedbackResult

    def update_learning_state(
        self,
        feedback: FeedbackResult
    ) -> None

    def get_feedback_stats(self) -> FeedbackStats
```

**Performance Target**: <20ms per feedback event

### 5. Mnemosyne Integration

**Purpose**: Persistent cross-session learning and agentic orchestration

**Memory Storage**:
- **Patterns**: Learned patterns with scores
- **Constraints**: Soft constraints with weights
- **Project Profiles**: Project-specific conventions
- **Feedback History**: Generation outcomes and scores
- **Adaptation Metrics**: Learning progress over time

**Memory Namespace**:
```
project:<name>:patterns           # Project patterns
project:<name>:constraints        # Learned constraints
project:<name>:profile            # Project profile
project:<name>:feedback           # Feedback history
global:patterns                   # Cross-project patterns
```

**Memory Operations**:
- Store learned patterns after successful generations
- Recall patterns when generating for similar context
- Evolve patterns (consolidation, decay, archival)
- Orchestrate multi-agent learning workflows

**Interface**:
```python
class MnemosyneIntegration:
    def store_pattern(
        self,
        pattern: Pattern,
        namespace: str,
        importance: int
    ) -> None

    def recall_patterns(
        self,
        context: GenerationContext,
        limit: int = 10
    ) -> list[ScoredPattern]

    def update_pattern_score(
        self,
        pattern_id: str,
        delta: float
    ) -> None

    def evolve_memories(self) -> EvolutionStats

    def orchestrate_learning(
        self,
        task: LearningTask
    ) -> OrchestrationResult
```

**Performance Target**: <100ms pattern recall

### 6. Hybrid Constraint Weighting

**Purpose**: Combine hard and soft constraints with temperature control

**Weighting Strategy**:
- Hard constraints: Binary mask (always enforced)
- Soft constraints: Probability weights (preferences)
- Temperature: Control strictness vs. creativity

**Temperature Modes**:
- `0.0`: Hard constraints only (maximum safety)
- `0.5`: Balanced (prefer learned patterns)
- `1.0`: Creative (allow deviation from patterns)

**Interface**:
```python
class HybridConstraintWeighter:
    def combine_constraints(
        self,
        hard: ConstraintSet,
        soft: ConstraintSet,
        temperature: float = 0.5
    ) -> WeightedConstraintSet

    def compute_token_weights(
        self,
        weighted_constraints: WeightedConstraintSet,
        current_state: GenerationState
    ) -> TokenWeights

    def apply_temperature(
        self,
        weights: TokenWeights,
        temperature: float
    ) -> TokenWeights
```

## Dependencies

**Phase 2 (Complete)**:
- GrammarBuilder for constraint synthesis
- SchemaBuilder for JSON constraints
- Language templates

**Phase 3 (Complete)**:
- TypeInferenceEngine for type-based patterns
- InhabitationSolver for type-driven completions
- TypeToGrammarConverter

**Phase 4 (Complete)**:
- ValidationPipeline for feedback
- RepairOrchestrator for success/failure tracking
- PedanticRavenIntegration for quality scoring

**External**:
- mnemosyne for persistent memory
- Tree-sitter for AST parsing
- Language-specific pattern extractors

## Test Plan

### Unit Tests (Target: 90+ tests, 85%+ coverage)

1. **Pattern Mining** (20 tests)
   - Syntactic pattern extraction
   - Type pattern extraction
   - Semantic pattern extraction
   - Pattern ranking
   - Incremental mining
   - Large codebase handling

2. **Constraint Learning** (20 tests)
   - Learn from success
   - Learn from failure
   - Weight updates
   - Constraint pruning
   - Multi-source learning
   - Feedback integration

3. **Project Adaptation** (15 tests)
   - Project initialization
   - Convention extraction
   - Constraint creation
   - Feedback updates
   - Adaptation stats

4. **Feedback Loop** (15 tests)
   - Feedback collection
   - Feedback classification
   - Score updates
   - Pattern persistence
   - Stats tracking

5. **Mnemosyne Integration** (15 tests)
   - Pattern storage
   - Pattern recall
   - Score updates
   - Memory evolution
   - Namespace management

6. **Hybrid Weighting** (10 tests)
   - Constraint combination
   - Temperature application
   - Token weight computation
   - Mode transitions

7. **Integration Tests** (15 tests)
   - End-to-end learning workflow
   - Cross-session persistence
   - Multi-project learning
   - Performance benchmarks
   - Quality improvement metrics

### Performance Tests

- Pattern mining: <5s for 100K LOC
- Pattern lookup: <50ms
- Learning update: <10ms
- Feedback processing: <20ms
- mnemosyne recall: <100ms
- Generation overhead: <10%

### Quality Tests

- Learning improvement: >10% after 100 examples
- Pattern recall accuracy: >90%
- Adaptation convergence: <100 examples
- Cross-session retention: >95%

### Coverage Targets

- Critical path (feedback loop, learning): 90%+
- Business logic (pattern mining, adaptation): 85%+
- Overall: 80%+

## Implementation Plan

### Subtasks (Dependency Order)

1. **maze-zih.5.1**: Pattern mining engine
   - Multi-level pattern extraction
   - Frequency analysis
   - Pattern ranking
   - 20 tests

2. **maze-zih.5.2**: Constraint learning system
   - Learning from feedback
   - Weight updates
   - Constraint pruning
   - 20 tests

3. **maze-zih.5.3**: Project adaptation manager
   - Project initialization
   - Convention extraction
   - Adapted constraints
   - 15 tests

4. **maze-zih.5.4**: Feedback loop orchestrator
   - Feedback collection
   - Score updates
   - Stats tracking
   - 15 tests

5. **maze-zih.5.5**: Mnemosyne integration
   - Pattern storage/recall
   - Memory evolution
   - Orchestration hooks
   - 15 tests

6. **maze-zih.5.6**: Hybrid constraint weighting
   - Weight combination
   - Temperature control
   - Token weights
   - 10 tests

7. **maze-zih.5.7**: Integration and benchmarks
   - End-to-end workflows
   - Performance optimization
   - Quality metrics
   - Documentation
   - 15 tests

### Parallelization Opportunities

**Stream A** (Pattern Extraction):
- maze-zih.5.1 (pattern mining)

**Stream B** (Learning Systems):
- maze-zih.5.2 (constraint learning)
- maze-zih.5.3 (project adaptation)

**Stream C** (Integration):
- maze-zih.5.5 (mnemosyne integration)

**Sequential** (Orchestration):
- maze-zih.5.4 (feedback loop) - depends on A + B
- maze-zih.5.6 (hybrid weighting) - depends on B
- maze-zih.5.7 (integration) - depends on all

## Typed Holes (Interfaces)

### PatternMiningEngine ↔ ConstraintLearningSystem
```python
# PatternMiningEngine provides patterns for learning
patterns = mining_engine.mine_patterns(project_path, language)
constraints = learning_system.create_constraints_from_patterns(patterns)
```

### ConstraintLearningSystem ↔ FeedbackLoopOrchestrator
```python
# Orchestrator provides feedback to learner
feedback_result = orchestrator.process_feedback(generation, validation)
learning_system.update_weights(feedback_result.pattern, feedback_result.score)
```

### ProjectAdaptationManager ↔ MnemosyneIntegration
```python
# Adapter persists to mnemosyne
profile = adapter.initialize_project(project_path)
memory.store_pattern(profile, f"project:{project_name}:profile", importance=9)
```

### FeedbackLoopOrchestrator ↔ All Components
```python
# Orchestrates all learning components
orchestrator = FeedbackLoopOrchestrator(
    learner=constraint_learner,
    adapter=project_adapter,
    memory=mnemosyne_integration
)

result = orchestrator.process_feedback(generation, validation, repair)
```

## Edge Cases

1. **Cold start**: No patterns available for new project → fallback to global patterns
2. **Pattern conflicts**: Multiple patterns apply → rank by score and recency
3. **Over-fitting**: Too specific patterns → use temperature to allow creativity
4. **Memory exhaustion**: Too many patterns → prune low-scoring patterns
5. **Cross-project pollution**: Wrong patterns recalled → namespace isolation
6. **Stale patterns**: Outdated conventions → decay mechanism
7. **Performance degradation**: Too many soft constraints → adaptive filtering

## Success Criteria

- [ ] All subtasks (maze-zih.5.1 through maze-zih.5.7) complete
- [ ] 90+ tests passing
- [ ] 80%+ test coverage
- [ ] Pattern mining <5s for 100K LOC
- [ ] Pattern lookup <50ms
- [ ] Learning update <10ms
- [ ] >10% quality improvement after 100 examples
- [ ] >90% pattern recall accuracy
- [ ] Documentation complete
- [ ] No TODO/FIXME/stub comments

## References

- **Adaptive Constraint-Based Code Generation** (Technical Proposal): Pattern mining and adaptive learning design
- **DiffuCoder** (Apple, 2024): Speculative decoding with correctness guarantees
- **Mnemosyne**: Semantic memory and orchestration system
- **LLGuidance**: Fast constraint enforcement framework
- **Code Pattern Mining** (MSR research): Frequent pattern extraction techniques

## Metrics and Monitoring

### Quality Metrics
- Compilation success rate improvement
- Test pass rate improvement
- Validation success rate improvement
- Security violation reduction
- Code quality score improvement

### Learning Metrics
- Patterns learned per session
- Patterns reused successfully
- Adaptation convergence speed
- Cross-session retention rate
- Pattern precision/recall

### Performance Metrics
- Mining time per LOC
- Pattern lookup latency
- Learning update latency
- Generation overhead
- Memory usage

## Phase Transition

**Entry Criteria** (from Phase 4):
- ✅ ValidationPipeline complete
- ✅ RepairOrchestrator working
- ✅ PedanticRavenIntegration functional
- ✅ Feedback mechanisms in place

**Exit Criteria** (to Phase 6):
- [ ] Pattern mining engine complete
- [ ] Constraint learning working
- [ ] Project adaptation functional
- [ ] Feedback loop orchestrated
- [ ] mnemosyne integration complete
- [ ] Hybrid weighting operational
- [ ] Quality improvement demonstrated
- [ ] All tests passing
