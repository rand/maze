# Phase 5: Adaptive Learning - Execution Plan

> **Purpose**: Detailed execution plan for Phase 5 implementation with task ordering, time estimates, parallelization strategy, and risk mitigation.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Task Breakdown](#2-task-breakdown)
3. [Dependency Analysis](#3-dependency-analysis)
4. [Parallel Execution Strategy](#4-parallel-execution-strategy)
5. [Critical Path](#5-critical-path)
6. [Time Estimates](#6-time-estimates)
7. [Resource Requirements](#7-resource-requirements)
8. [Risk Mitigation](#8-risk-mitigation)
9. [Implementation Checklist](#9-implementation-checklist)

---

## 1. Executive Summary

### Goals
- Implement adaptive learning system for Maze
- Enable >10% quality improvement through learning
- Achieve <100 examples for project adaptation convergence
- Integrate with mnemosyne for persistent cross-session learning

### Scope
- 7 subtasks (maze-zih.5.1 through maze-zih.5.7)
- 110 comprehensive tests
- 6 core components + integration
- ~3,500 lines of production code

### Timeline
- **Estimated Duration**: 12-18 hours (with parallelization)
- **Sequential Duration**: 20-25 hours
- **Target Completion**: Single focused session or 2-3 sessions

### Success Criteria
- All 110 tests passing
- 85%+ code coverage
- >10% quality improvement demonstrated
- Pattern recall <100ms
- Documentation complete

---

## 2. Task Breakdown

### 2.1 maze-zih.5.1: Pattern Mining Engine

**Subtask**: Implement pattern extraction from codebases

**Components**:
- `PatternMiningEngine` class
- Syntactic pattern extraction
- Type pattern extraction
- Semantic pattern extraction
- Pattern ranking
- Incremental mining
- Performance optimization

**Files**:
- `src/maze/learning/pattern_mining.py` (main implementation)
- `tests/unit/test_learning/test_pattern_mining.py` (20 tests)

**Dependencies**:
- Phase 3 (type_system for TypeContext)
- Tree-sitter for AST parsing

**Test Count**: 20 tests

**Estimated Time**: 3-4 hours

**Deliverables**:
- Working pattern mining engine
- Support for Python, TypeScript, Rust, Go, Zig
- Performance: <5s for 100K LOC
- All 20 unit tests passing

---

### 2.2 maze-zih.5.2: Constraint Learning System

**Subtask**: Implement learning from generation feedback

**Components**:
- `ConstraintLearningSystem` class
- Learning from success/failure
- Weight updates
- Constraint pruning
- Learning history tracking

**Files**:
- `src/maze/learning/constraint_learning.py` (main implementation)
- `tests/unit/test_learning/test_constraint_learning.py` (20 tests)

**Dependencies**:
- Phase 2 (synthesis for ConstraintSet)
- Phase 4 (validation for ValidationResult)
- maze-zih.5.1 (pattern mining for pattern extraction)

**Test Count**: 20 tests

**Estimated Time**: 3-4 hours

**Deliverables**:
- Working constraint learning system
- Learning from positive and negative feedback
- Weight update algorithm with learning rate
- Performance: <10ms per update
- All 20 unit tests passing

---

### 2.3 maze-zih.5.3: Project Adaptation Manager

**Subtask**: Implement project-specific adaptation

**Components**:
- `ProjectAdaptationManager` class
- Project initialization
- Convention extraction
- Adapted constraint creation
- Convergence tracking

**Files**:
- `src/maze/learning/project_adaptation.py` (main implementation)
- `tests/unit/test_learning/test_project_adaptation.py` (15 tests)

**Dependencies**:
- maze-zih.5.1 (pattern mining)
- maze-zih.5.2 (constraint learning)

**Test Count**: 15 tests

**Estimated Time**: 2.5-3 hours

**Deliverables**:
- Working project adaptation
- Convention extraction (naming, structure, testing, API usage)
- Adapted constraints from conventions
- Performance: <30s initialization
- All 15 unit tests passing

---

### 2.4 maze-zih.5.4: Feedback Loop Orchestrator

**Subtask**: Coordinate learning from all sources

**Components**:
- `FeedbackLoopOrchestrator` class
- Feedback processing
- Multi-source learning coordination
- Statistics tracking
- Auto-persistence to mnemosyne

**Files**:
- `src/maze/learning/feedback_loop.py` (main implementation)
- `tests/unit/test_learning/test_feedback_loop.py` (15 tests)

**Dependencies**:
- maze-zih.5.2 (constraint learning)
- maze-zih.5.3 (project adaptation)
- maze-zih.5.5 (mnemosyne integration)
- Phase 4 (validation and repair results)

**Test Count**: 15 tests

**Estimated Time**: 2.5-3 hours

**Deliverables**:
- Working feedback orchestrator
- Integrated learning from all sources
- Performance: <20ms per feedback event
- Auto-persistence integration
- All 15 unit tests passing

---

### 2.5 maze-zih.5.5: Mnemosyne Integration

**Subtask**: Persistent cross-session learning

**Components**:
- `MnemosyneIntegration` class
- Pattern storage/recall
- Score updates
- Memory evolution
- Orchestration hooks (optional)

**Files**:
- `src/maze/integrations/mnemosyne/__init__.py` (main implementation)
- `tests/unit/test_integrations/test_mnemosyne.py` (15 tests)

**Dependencies**:
- mnemosyne CLI installed
- Pattern data structures from maze-zih.5.1

**Test Count**: 15 tests

**Estimated Time**: 2-2.5 hours

**Deliverables**:
- Working mnemosyne integration
- Pattern storage and recall
- Performance: <100ms recall
- Namespace management
- All 15 unit tests passing

---

### 2.6 maze-zih.5.6: Hybrid Constraint Weighting

**Subtask**: Combine hard and soft constraints

**Components**:
- `HybridConstraintWeighter` class
- Constraint combination
- Token weight computation
- Temperature control

**Files**:
- `src/maze/learning/hybrid_weighting.py` (main implementation)
- `tests/unit/test_learning/test_hybrid_weighting.py` (10 tests)

**Dependencies**:
- Phase 2 (synthesis for ConstraintSet)
- maze-zih.5.2 (learned constraints)

**Test Count**: 10 tests

**Estimated Time**: 1.5-2 hours

**Deliverables**:
- Working hybrid weighting
- Hard/soft constraint combination
- Temperature modes (0, 0.5, 1.0)
- Performance: <10ms token weights
- All 10 unit tests passing

---

### 2.7 maze-zih.5.7: Integration and Benchmarks

**Subtask**: End-to-end integration and quality validation

**Components**:
- Integration tests
- Performance benchmarks
- Quality improvement metrics
- Documentation

**Files**:
- `tests/integration/test_adaptive_learning_integration.py` (15 tests)
- `benchmarks/adaptive_learning_benchmark.py`
- `src/maze/learning/README.md`
- `src/maze/learning/API.md`

**Dependencies**:
- All previous subtasks (5.1-5.6)

**Test Count**: 15 tests

**Estimated Time**: 3-4 hours

**Deliverables**:
- End-to-end workflows tested
- Quality improvement >10% demonstrated
- Pattern recall accuracy >90%
- Adaptation convergence <100 examples
- Complete documentation
- All 15 integration tests passing

---

## 3. Dependency Analysis

### Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                      External Dependencies                   │
│  (Phase 2, Phase 3, Phase 4, mnemosyne, tree-sitter)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┼───────────┐
           │           │           │
           ▼           ▼           ▼
      ┌────────┐  ┌────────┐  ┌────────┐
      │  5.1   │  │  5.5   │  │  5.6   │  ← Independent (can parallelize)
      │Pattern │  │Mnemosyn│  │Hybrid  │
      │Mining  │  │  e     │  │Weightin│
      └───┬────┘  └────────┘  └───┬────┘
          │                        │
          ▼                        │
      ┌────────┐                   │
      │  5.2   │                   │
      │Constrai│                   │
      │Learning│◄──────────────────┘
      └───┬────┘
          │
          ▼
      ┌────────┐
      │  5.3   │
      │Project │
      │Adaptati│
      └───┬────┘
          │
          └──────┐
                 │
         ┌───────▼────────┐
         │      5.4       │
         │    Feedback    │
         │      Loop      │
         └───────┬────────┘
                 │
                 ▼
         ┌───────────────┐
         │      5.7      │
         │  Integration  │
         └───────────────┘
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|------------|--------|
| 5.1 Pattern Mining | Phase 3 | 5.2, 5.3 |
| 5.2 Constraint Learning | Phase 2, Phase 4, 5.1 | 5.3, 5.4, 5.6 |
| 5.3 Project Adaptation | 5.1, 5.2 | 5.4 |
| 5.4 Feedback Loop | 5.2, 5.3, 5.5, Phase 4 | 5.7 |
| 5.5 Mnemosyne Integration | - | 5.4 |
| 5.6 Hybrid Weighting | Phase 2, 5.2 | 5.7 |
| 5.7 Integration | 5.1, 5.2, 5.3, 5.4, 5.5, 5.6 | - |

---

## 4. Parallel Execution Strategy

### Parallel Streams

**Stream A: Pattern Extraction**
```
5.1 Pattern Mining (3-4h)
   │
   ▼
5.2 Constraint Learning (3-4h)
   │
   ▼
5.3 Project Adaptation (2.5-3h)
```
**Total: 9-11 hours sequential**

**Stream B: Integration Infrastructure**
```
5.5 Mnemosyne Integration (2-2.5h)
   │
   (waits for Stream A to reach 5.2)
```
**Total: 2-2.5 hours**

**Stream C: Weighting System**
```
5.6 Hybrid Weighting (1.5-2h)
   │
   (waits for Stream A to reach 5.2)
```
**Total: 1.5-2 hours**

**Final Sequential**:
```
5.4 Feedback Loop (2.5-3h) ← requires A, B
   │
   ▼
5.7 Integration (3-4h) ← requires all
```
**Total: 5.5-7 hours**

### Parallelization Plan

**Phase 1** (Parallel):
- **Start 5.1** (Pattern Mining)
- **Start 5.5** (Mnemosyne Integration) ← Independent

**Phase 2** (Parallel, after 5.1 completes):
- **Start 5.2** (Constraint Learning) ← depends on 5.1
- **Start 5.6** (Hybrid Weighting) ← independent of 5.2 initially

**Phase 3** (After 5.2 completes):
- **Start 5.3** (Project Adaptation) ← depends on 5.2

**Phase 4** (After 5.2, 5.3, 5.5 complete):
- **Start 5.4** (Feedback Loop) ← depends on 5.2, 5.3, 5.5

**Phase 5** (After all complete):
- **Start 5.7** (Integration) ← depends on all

### Time Savings with Parallelization

- **Sequential Total**: 20-25 hours
- **Parallel Total**: 12-18 hours
- **Time Saved**: 8-7 hours (35-40% faster)

---

## 5. Critical Path

### Critical Path Sequence

```
5.1 Pattern Mining (3-4h)
   ↓
5.2 Constraint Learning (3-4h)
   ↓
5.3 Project Adaptation (2.5-3h)
   ↓
5.4 Feedback Loop (2.5-3h)
   ↓
5.7 Integration (3-4h)
```

**Critical Path Duration**: 14.5-18 hours

**Critical Path Tasks**: 5.1 → 5.2 → 5.3 → 5.4 → 5.7

### Off Critical Path

- **5.5 Mnemosyne Integration**: Can complete while 5.1-5.3 are running
- **5.6 Hybrid Weighting**: Can complete while 5.3 is running

### Optimization Opportunities

1. **Start 5.5 immediately** (independent)
2. **Start 5.6 as soon as 5.2 begins** (minimal dependency)
3. **Ensure 5.1 completes quickly** (blocks critical path)
4. **Parallelize tests** within each task

---

## 6. Time Estimates

### Per-Task Estimates

| Task ID | Task Name | Estimated Time | Tests | Lines of Code |
|---------|-----------|----------------|-------|---------------|
| 5.1 | Pattern Mining Engine | 3-4 hours | 20 | ~600 |
| 5.2 | Constraint Learning System | 3-4 hours | 20 | ~500 |
| 5.3 | Project Adaptation Manager | 2.5-3 hours | 15 | ~400 |
| 5.4 | Feedback Loop Orchestrator | 2.5-3 hours | 15 | ~350 |
| 5.5 | Mnemosyne Integration | 2-2.5 hours | 15 | ~300 |
| 5.6 | Hybrid Constraint Weighting | 1.5-2 hours | 10 | ~250 |
| 5.7 | Integration & Benchmarks | 3-4 hours | 15 | ~600 |
| **Total** | **All Tasks** | **18-23 hours** | **110** | **~3,000** |

### Time Distribution

**Development**: 60% (11-14 hours)
**Testing**: 25% (4.5-5.5 hours)
**Documentation**: 10% (1.8-2.3 hours)
**Debugging**: 5% (0.9-1.2 hours)

### Milestone Timeline

| Milestone | Tasks Complete | Cumulative Time | Percentage |
|-----------|----------------|-----------------|------------|
| Pattern extraction working | 5.1 | 3-4h | 17-21% |
| Learning system functional | 5.1, 5.2 | 6-8h | 33-42% |
| Project adaptation working | 5.1, 5.2, 5.3 | 8.5-11h | 47-58% |
| Integration complete | 5.5 | +2-2.5h | - |
| Weighting complete | 5.6 | +1.5-2h | - |
| Feedback loop working | 5.4 | +2.5-3h | 71-79% |
| All tests passing | 5.7 | +3-4h | 100% |

---

## 7. Resource Requirements

### Development Environment

**Required**:
- Python 3.11+ with uv package manager
- mnemosyne CLI installed and configured
- Tree-sitter with language bindings (Python, TypeScript, Rust)
- Phase 2, 3, 4 components complete

**Optional**:
- Multiple terminal sessions for parallel work
- Code editor with type checking (VS Code, PyCharm)

### External Dependencies

**Python Packages**:
```toml
[dependencies]
tree-sitter = "^0.20.0"
tree-sitter-python = "^0.20.0"
tree-sitter-typescript = "^0.20.0"
tree-sitter-rust = "^0.20.0"
```

**System Tools**:
```bash
# mnemosyne
mnemosyne --version  # Required

# Language tools (for pattern extraction)
python --version     # 3.11+
node --version       # For TypeScript parsing
cargo --version      # For Rust parsing
```

### Test Data

**Codebases for Testing**:
- Small: ~1K LOC Python/TypeScript
- Medium: ~10K LOC multi-language
- Large: ~100K LOC for performance tests

**Pre-generate test data**:
```bash
# Create test fixtures
mkdir -p tests/fixtures/codebases/{small,medium,large}

# Small test codebase (can generate)
# Medium test codebase (can use existing project subset)
# Large test codebase (need realistic project)
```

### Hardware Requirements

**Minimum**:
- 8GB RAM
- 4 CPU cores
- 1GB disk space

**Recommended**:
- 16GB RAM (for large codebase mining)
- 8 CPU cores (for parallel processing)
- 2GB disk space (for test fixtures + cache)

---

## 8. Risk Mitigation

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Pattern mining performance | Medium | High | Implement parallel processing, caching, incremental updates |
| mnemosyne availability | Low | Medium | Graceful degradation, local cache fallback |
| Learning convergence | Medium | High | Adaptive learning rate, diverse test cases |
| Integration complexity | High | Medium | Incremental integration, comprehensive tests |
| Test data quality | Medium | Medium | Generate diverse fixtures, use real codebases |
| Time overrun | Medium | Low | Parallel execution, focus on critical path |

### Detailed Mitigations

#### 1. Pattern Mining Performance

**Risk**: Mining large codebases exceeds 5s target.

**Mitigation**:
```python
# Parallel processing
from concurrent.futures import ProcessPoolExecutor

def mine_patterns_parallel(files: list[Path]) -> PatternSet:
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = executor.map(extract_patterns_from_file, files)
    return aggregate_patterns(results)

# Incremental caching
def mine_with_cache(codebase: Path) -> PatternSet:
    cache_file = codebase / ".maze_patterns_cache.json"
    if cache_file.exists():
        return load_cached_patterns(cache_file)
    patterns = mine_patterns(codebase)
    save_cache(patterns, cache_file)
    return patterns
```

#### 2. mnemosyne Availability

**Risk**: mnemosyne CLI not installed or fails.

**Mitigation**:
```python
def _ensure_mnemosyne_available(self) -> bool:
    """Check mnemosyne availability."""
    try:
        result = subprocess.run(
            ["mnemosyne", "--version"],
            capture_output=True,
            timeout=1
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("mnemosyne not available, using local cache only")
        return False

# Fallback to local storage
if not self._ensure_mnemosyne_available():
    self.use_local_cache = True
```

#### 3. Learning Convergence

**Risk**: Learning does not improve quality within 100 examples.

**Mitigation**:
```python
def _adaptive_learning_rate(self, iteration: int) -> float:
    """Adjust learning rate based on progress."""
    if iteration < 10:
        return 0.1  # Fast initial learning
    elif iteration < 50:
        return 0.05  # Moderate learning
    else:
        return 0.01  # Fine-tuning

def _monitor_convergence(self) -> bool:
    """Check if learning has converged."""
    if len(self.quality_history) < 10:
        return False

    recent = self.quality_history[-10:]
    variance = np.var(recent)

    # Converged if variance is low
    return variance < 0.01
```

#### 4. Integration Complexity

**Risk**: Components don't integrate smoothly.

**Mitigation**:
- **Incremental integration**: Integrate one component at a time
- **Interface contracts**: Use Protocol classes for clear contracts
- **Mock dependencies**: Test each component in isolation first
- **Integration tests early**: Write integration tests before full implementation

#### 5. Test Data Quality

**Risk**: Test fixtures don't represent real codebases.

**Mitigation**:
```bash
# Use real open-source projects for testing
git clone https://github.com/python/cpython.git tests/fixtures/codebases/large/cpython
git clone https://github.com/microsoft/TypeScript.git tests/fixtures/codebases/large/typescript

# Generate diverse synthetic fixtures
python scripts/generate_test_fixtures.py --diversity high --count 50
```

---

## 9. Implementation Checklist

### Pre-Implementation

- [ ] Review Phase 2, 3, 4 implementations
- [ ] Verify mnemosyne installation (`mnemosyne --version`)
- [ ] Install tree-sitter language bindings
- [ ] Create test fixtures directories
- [ ] Set up development environment

### Implementation Order

#### Week 1, Day 1-2: Core Pattern Extraction

- [ ] **Task 5.1**: Pattern Mining Engine
  - [ ] Create `src/maze/learning/__init__.py`
  - [ ] Implement `pattern_mining.py`
  - [ ] Syntactic pattern extraction
  - [ ] Type pattern extraction
  - [ ] Semantic pattern extraction
  - [ ] Pattern ranking
  - [ ] Write 20 unit tests
  - [ ] Verify performance (<5s for 100K LOC)
  - [ ] Commit: "Implement Pattern Mining Engine (maze-zih.5.1)"

- [ ] **Task 5.5** (Parallel): Mnemosyne Integration
  - [ ] Create `src/maze/integrations/mnemosyne/__init__.py`
  - [ ] Implement pattern storage
  - [ ] Implement pattern recall
  - [ ] Write 15 unit tests
  - [ ] Verify performance (<100ms recall)
  - [ ] Commit: "Implement Mnemosyne Integration (maze-zih.5.5)"

#### Week 1, Day 2-3: Learning Systems

- [ ] **Task 5.2**: Constraint Learning System
  - [ ] Implement `constraint_learning.py`
  - [ ] Learning from success/failure
  - [ ] Weight updates
  - [ ] Constraint pruning
  - [ ] Write 20 unit tests
  - [ ] Verify performance (<10ms per update)
  - [ ] Commit: "Implement Constraint Learning System (maze-zih.5.2)"

- [ ] **Task 5.6** (Parallel): Hybrid Weighting
  - [ ] Implement `hybrid_weighting.py`
  - [ ] Constraint combination
  - [ ] Temperature control
  - [ ] Write 10 unit tests
  - [ ] Verify performance (<10ms token weights)
  - [ ] Commit: "Implement Hybrid Constraint Weighting (maze-zih.5.6)"

#### Week 1, Day 3-4: Adaptation and Orchestration

- [ ] **Task 5.3**: Project Adaptation Manager
  - [ ] Implement `project_adaptation.py`
  - [ ] Project initialization
  - [ ] Convention extraction
  - [ ] Write 15 unit tests
  - [ ] Verify performance (<30s initialization)
  - [ ] Commit: "Implement Project Adaptation Manager (maze-zih.5.3)"

- [ ] **Task 5.4**: Feedback Loop Orchestrator
  - [ ] Implement `feedback_loop.py`
  - [ ] Feedback processing
  - [ ] Multi-source integration
  - [ ] Write 15 unit tests
  - [ ] Verify performance (<20ms per feedback)
  - [ ] Commit: "Implement Feedback Loop Orchestrator (maze-zih.5.4)"

#### Week 1, Day 4-5: Integration and Documentation

- [ ] **Task 5.7**: Integration and Benchmarks
  - [ ] Write 15 integration tests
  - [ ] Implement performance benchmarks
  - [ ] Verify quality improvement >10%
  - [ ] Verify pattern recall accuracy >90%
  - [ ] Verify convergence <100 examples
  - [ ] Create README.md
  - [ ] Create API.md
  - [ ] Commit: "Complete Phase 5 integration and documentation (maze-zih.5.7)"

### Post-Implementation

- [ ] Run full test suite (`uv run pytest tests/unit/test_learning/`)
- [ ] Run integration tests (`uv run pytest tests/integration/test_adaptive_learning_integration.py`)
- [ ] Run benchmarks (`uv run python benchmarks/adaptive_learning_benchmark.py`)
- [ ] Verify all 110 tests passing
- [ ] Verify 85%+ code coverage
- [ ] Push all commits
- [ ] Close Phase 5 Beads issues
- [ ] Update README.md roadmap (mark Phase 5 complete)

---

## Implementation Tips

### Commit Strategy

**Commit after each major milestone**:
1. After each subtask completion (7 commits minimum)
2. After test suite for each component (inline with implementation)
3. After documentation (final commit)

**Commit message format**:
```
Implement [Component] (maze-zih.5.X)

[Brief description of what was implemented]

- Feature 1
- Feature 2
- X tests passing
- Performance target: [target]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Testing Strategy

**Test-Driven Development**:
1. Write test skeleton first
2. Implement until tests pass
3. Refactor while keeping tests green
4. Add edge case tests

**Test Execution**:
```bash
# Run tests for current task
uv run pytest tests/unit/test_learning/test_pattern_mining.py -v

# Run with coverage
uv run pytest tests/unit/test_learning/ --cov=maze.learning --cov-report=term

# Run integration tests
uv run pytest tests/integration/test_adaptive_learning_integration.py -v

# Run benchmarks
uv run python benchmarks/adaptive_learning_benchmark.py
```

### Performance Optimization

**Profile before optimizing**:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = pattern_miner.mine_patterns(codebase, language)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

**Use caching aggressively**:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def extract_pattern(code_hash: str) -> Pattern:
    # Expensive extraction
    ...
```

---

## Summary

This execution plan provides:

1. **Detailed task breakdown** with 7 subtasks
2. **Dependency analysis** showing critical path
3. **Parallel execution strategy** saving 35-40% time
4. **Time estimates** totaling 12-18 hours (parallel)
5. **Resource requirements** for successful implementation
6. **Risk mitigation** for 6 major risks
7. **Implementation checklist** with step-by-step guidance

**Critical Path**: 5.1 → 5.2 → 5.3 → 5.4 → 5.7 (14.5-18 hours)

**Parallel Opportunities**:
- Start 5.5 (Mnemosyne) immediately
- Start 5.6 (Hybrid Weighting) after 5.2 begins

**Next Step**: Begin implementation with maze-zih.5.1 (Pattern Mining Engine)
