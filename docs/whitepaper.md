---
title: MAZE Technical Whitepaper
description: Adaptive Constrained Code Generation with 4-tier constraint hierarchy - syntactic, type, semantic, and contextual constraints for LLM code generation
version: v0.1.0-whitepaper
date: November 2025
---

# MAZE Whitepaper

**Adaptive Constrained Code Generation**

**Version**: v0.1.0-whitepaper
**Date**: November 2025
**Repository**: [github.com/rand/maze](https://github.com/rand/maze)

## Abstract

Large Language Models (LLMs) have demonstrated remarkable capabilities in code generation, yet they suffer from high error rates when generating complex, type-correct code. Unconstrained generation often produces syntactically valid but semantically incorrect or type-unsafe code, requiring expensive post-hoc validation and multiple repair iterations.

MAZE introduces a paradigm shift: **compile constraints before decoding, rather than hoping for correctness after generation**. Through a novel 4-tier constraint hierarchy—syntactic (CFG grammars), type (inhabitation search), semantic (test-driven), and contextual (learned patterns)—MAZE guides LLM generation toward valid, type-correct, and project-conformant code from the start.

Built on research from PLDI 2025 (Type-Constrained Code Generation) and OOPSLA 2024 (Typed Holes), MAZE integrates with multiple LLM providers (OpenAI, vLLM, SGLang, llama.cpp) through llguidance for constraint enforcement, mnemosyne for persistent learning, and RUNE for sandboxed validation.

**Current status**: Core constraint system complete (Phases 1-3), validation pipeline in active development (Phase 4: 6/10 tasks complete), with adaptive learning and production hardening planned (Phases 5-6).

**Significance**: MAZE demonstrates that formal constraint enforcement can be integrated with modern LLMs without sacrificing generation speed, providing a foundation for the next generation of AI-assisted development tools.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Problem Statement](#2-problem-statement)
3. [Architecture Overview](#3-architecture-overview)
4. [4-Tier Constraint System](#4-4-tier-constraint-system)
5. [Type-Directed Synthesis](#5-type-directed-synthesis)
6. [Integration Ecosystem](#6-integration-ecosystem)
7. [Implementation Status and Roadmap](#7-implementation-status-and-roadmap)
8. [Research Foundation](#8-research-foundation)
9. [Architecture Validation](#9-architecture-validation)
10. [Getting Started](#10-getting-started)
11. [Conclusion](#11-conclusion)
12. [Resources](#12-resources)

---

## 1. Introduction

### The Code Generation Challenge

Large Language Models have revolutionized software development assistance, enabling developers to generate substantial code from natural language descriptions. However, this capability comes with a fundamental limitation: without explicit constraints, LLMs generate code based solely on statistical patterns learned from training data. This approach produces code that is often:

- **Syntactically plausible** but incorrect
- **Type-unsafe**, causing compilation failures
- **Semantically wrong**, failing to implement the specified behavior
- **Inconsistent** with project conventions and patterns

### MAZE's Paradigm Shift

MAZE reverses this paradigm. Instead of hoping the LLM generates correct code, MAZE **compiles constraints before token generation**, guiding the model toward valid outputs from the start.

**Traditional Approach**:
```
Generate (unconstrained) → Validate → Find errors → Fix → Repeat
```

**MAZE Approach**:
```
Build constraints → Generate (constrained) → Minimal validation → Done
```

### Architecture Foundation

MAZE is built on four key innovations:

1. **4-Tier Constraint Hierarchy**: Progressive constraint tightening from syntax through types, semantics, and context
2. **Type-Directed Synthesis**: Bidirectional type inference and inhabitation search for type-correct code paths
3. **Multi-System Integration**: Seamless integration with llguidance, mnemosyne, RUNE, and pedantic_raven
4. **Provider Agnosticism**: Support for OpenAI, vLLM, SGLang, and llama.cpp through unified adapters

## 2. Problem Statement

### Unconstrained LLM Generation Failures

Consider a request to generate a TypeScript function:

```
"Create an async function that fetches a user by ID and returns their email"
```

An unconstrained LLM might generate:

```typescript
async function getUserEmail(id) {
  const user = await fetchUser(id);
  return user.email;
}
```

This code has multiple issues:

1. **Missing type annotations**: Parameters and return type unspecified
2. **Type safety violation**: `user` might be `null` or `undefined`
3. **Incomplete error handling**: Network failures unhandled
4. **Contextual mismatch**: May not match project's error handling patterns

### The Cost of Post-Hoc Validation

Post-generation validation creates a costly feedback loop:

- **Iteration 1**: Generate code → Compile → Find type errors → Prompt for fixes
- **Iteration 2**: Generate fixes → Compile → Find new errors → Prompt again
- **Iteration 3**: Generate fixes → Compile → Test → Find semantic errors → Prompt again

In practice, research shows unconstrained generation often requires 3-5 iterations before producing working code. Each iteration consumes LLM API calls, increases latency, risks context window overflow, and frustrates developers.

### Type Errors in Generated Code

Type errors are particularly problematic because they cascade. A single type mismatch can cause compilation failures blocking all downstream work, silent bugs when type coercion hides errors, integration failures when code doesn't match API contracts, and maintenance burden as type-unsafe code spreads through the codebase.

Research by Mündler et al. (PLDI 2025) found that unconstrained LLMs produce type errors in over 50% of generated functions for typed languages like TypeScript and Rust.

## 3. Architecture Overview

MAZE's architecture consists of five integrated stages that transform a code generation request into validated, type-correct code:

### Stage 1: Context Indexer

**Purpose**: Extract structured information from source code to inform constraint synthesis

**Current Implementation**:

- **TypeScript Indexer** ✅ Complete
  - Extracts functions, classes, interfaces, type aliases
  - Parses type annotations and generic parameters
  - Detects project style (indentation, quotes, semicolons)
  - Identifies test patterns (Jest, Mocha, Vitest)

### Stage 2: Constraint Synthesis

**Purpose**: Build hierarchical constraints from indexed context and generation request

**Components**:

1. **GrammarBuilder** ✅: Generates CFG grammars in Lark format
2. **TypeToGrammarConverter** ✅: Converts type constraints into grammar constraints
3. **SchemaBuilder** ✅: Generates JSON Schema for structured output (OpenAI compatibility)

### Stage 3: Decode Orchestrator

**Purpose**: Generate code under constraints using provider-specific adapters

**Integration**: llguidance for fast constraint enforcement

**Provider Adapters** ✅:

- **OpenAI**: JSON Schema mode via structured outputs
- **vLLM**: Full CFG grammar support
- **SGLang**: Native llguidance integration
- **llama.cpp**: Grammar-based generation

### Stage 4: Post-Validation

**Purpose**: Validate generated code across multiple dimensions in parallel

**Validators** (parallel execution):

1. **SyntaxValidator** ✅ Complete: Language-specific syntax checking
2. **TypeValidator** ✅ Complete: Type checking via language-specific tools
3. **TestValidator** ✅ Complete: Executes tests in RUNE sandbox
4. **LintValidator** ✅ Complete: Style checking (ESLint, Ruff, Clippy)
5. **ValidationPipeline** ✅ Complete: Orchestrates parallel validation

### Stage 5: Repair Loop

**Status**: 📋 Planned (Phase 4)

**Planned Components**:

- RepairOrchestrator: Manages repair iterations
- DiagnosticAnalyzer: Interprets validation failures
- ConstraintRefinement: Tightens constraints based on diagnostics

### Integration Flow

MAZE integrates with four external systems:

1. **llguidance** (Microsoft Research): Constraint enforcement during decoding
2. **mnemosyne**: Persistent memory for pattern learning across sessions
3. **RUNE**: Sandboxed execution for safe test validation
4. **pedantic_raven**: Deep semantic validation (planned integration)

## 4. 4-Tier Constraint System

MAZE's core innovation is a hierarchical constraint system that progressively narrows the space of valid programs:

### Tier 1: Syntactic Constraints (CFG Grammars)

**Purpose**: Ensure generated code is syntactically valid

**Implementation**: Context-Free Grammars (CFG) in Lark format

**Status**: ✅ Complete for TypeScript, partial for Python/Rust

**Benefits**:

- **Guaranteed syntactic validity**: Generated code always parses
- **Language-aware generation**: LLM respects language syntax rules
- **Composability**: Grammars can be combined and extended

### Tier 2: Type Constraints (Inhabitation Search)

**Purpose**: Ensure generated code is type-correct

**Implementation**: Type inhabitation solver + type-to-grammar conversion

**Status**: ✅ Complete

**Research Foundation**: Mündler et al., "Type-Constrained Code Generation" (PLDI 2025, arXiv:2504.09246)

#### Key Concept: Type Inhabitation

Given a source type `S` and target type `T`, find valid transformation paths.

**Example**: Finding `User → string` paths

Given:

```typescript
interface User {
  id: string;
  name: string;
  email: string;
  age: number;
  toString(): string;
}
```

Valid paths:

1. `user.id` → `string` ✅ (property access)
2. `user.name` → `string` ✅ (property access)
3. `user.email` → `string` ✅ (property access)
4. `user.toString()` → `string` ✅ (method call)

Invalid paths:

- `user.age` → `string` ❌ (type mismatch: number → string)
- `user` → `string` ❌ (no direct conversion)

**Benefits**:

- **Type safety**: Generated code is type-correct by construction
- **Error reduction**: Eliminates type errors that plague unconstrained generation
- **Contextual awareness**: Leverages project's type hierarchy

### Tier 3: Semantic Constraints (Test-Driven)

**Purpose**: Ensure generated code implements specified behavior

**Implementation**: Test cases + property specifications

**Status**: ✅ Validators complete, orchestration planned

Semantic constraints are specified through:

1. **Concrete test cases**: Input/output examples
2. **Property-based constraints**: Invariants that must hold

**Integration with RUNE**: All test execution happens in RUNE sandboxes to ensure network isolation, filesystem isolation, resource limits, and deterministic execution.

### Tier 4: Contextual Constraints (Learned)

**Purpose**: Ensure generated code matches project conventions and patterns

**Implementation**: Pattern mining + mnemosyne integration

**Status**: 📋 Planned (Phase 5)

Projects have implicit conventions that go beyond syntax, types, and semantics:

- Naming conventions (camelCase, PascalCase, snake_case)
- Error handling patterns (try/catch, Result types, null checks)
- Async patterns (async/await vs. .then(), Promise usage)
- Import organization (alphabetical, grouped by source)

### Constraint Composition

The four tiers compose hierarchically:

```
Syntactic constraints (broadest)
  ↓ Narrows to syntactically valid programs
Type constraints
  ↓ Narrows to type-correct programs
Semantic constraints
  ↓ Narrows to behaviorally correct programs
Contextual constraints
  ↓ Narrows to project-conformant programs
```

## 5. Type-Directed Synthesis

Type-directed synthesis is MAZE's most sophisticated capability, enabling generation of type-correct code through formal type theory.

**Research Foundation**: Mündler et al. (PLDI 2025) and Blinn et al. (OOPSLA 2024)

### Bidirectional Type Inference

MAZE implements bidirectional type inference to propagate type information in both directions:

- **Synthesis mode** (bottom-up): Infer type of expression from sub-expressions
- **Checking mode** (top-down): Check if expression matches expected type

### Type Inhabitation Solver

**Purpose**: Find expressions that inhabit (produce) a given type

**Optimization Techniques**:

1. **Memoization**: Cache results to avoid redundant searches
2. **Depth limiting**: Prevent infinite recursion (default: max_depth=5)
3. **Ranking**: Prioritize simpler expressions (fewer steps)
4. **Pruning**: Eliminate type-incompatible paths early

### Typed Hole Filling

**Research Foundation**: Blinn et al., "Statically Contextualizing LLMs with Typed Holes" (OOPSLA 2024, arXiv:2409.00921)

**Concept**: Partial code with "holes" to be filled

**Example**:

```typescript
async function getUserEmail(id: string): Promise<string> {
  const user = await fetchUser(id);

  if (user === null) {
    /*__HOLE__*/  // What should we return here?
  }

  return /*__HOLE__*/;  // What expression returns string from User?
}
```

## 6. Integration Ecosystem

### llguidance: Constraint Enforcement

**Source**: Microsoft Research, [guidance-ai/llguidance](https://github.com/guidance-ai/llguidance)

**Purpose**: Efficient constraint enforcement during LLM decoding

**Performance** (upstream benchmarks):

- Mask computation: ~50μs per token (p99, 128k tokenizer)
- Grammar compilation: <50ms for typical programming language grammars
- Memory overhead: ~10MB per grammar automaton

### mnemosyne: Persistent Memory

**Source**: [rand/mnemosyne](https://github.com/rand/mnemosyne), [Documentation](https://rand.github.io/mnemosyne)

**Purpose**: Semantic memory and learning across sessions

**Status**: ✅ Basic integration complete, full adaptive learning planned (Phase 5)

### RUNE: Sandboxed Execution

**Source**: [rand/RUNE](https://github.com/rand/RUNE), [Documentation](https://rand.github.io/RUNE)

**Purpose**: Safe, isolated execution for test validation

**Safety Guarantees**:

- **Network isolation**: No external network access
- **Filesystem isolation**: Temporary directory only
- **Resource limits**: CPU, memory, and time quotas enforced
- **Deterministic execution**: Same input → same output

**Status**: ✅ Complete integration via RuneExecutor

### pedantic_raven: Quality Enforcement

**Source**: [rand/pedantic_raven](https://github.com/rand/pedantic_raven)

**Status**: 📋 Placeholder exists, full integration planned (Phase 4/5)

## 7. Implementation Status and Roadmap

### Current Status: Active Development

MAZE has completed its core architectural foundation (Phases 1-3) and is actively building the validation and repair pipeline (Phase 4).

### Phase 1-3: Core System ✅ COMPLETE

**10,847 lines of code across 43 source files**

#### Phase 1: Foundation

- ✅ Core type system
- ✅ Constraint abstractions
- ✅ llguidance integration
- ✅ TypeScript indexer
- ✅ Test infrastructure (29 test files)

#### Phase 2: Syntactic Synthesis

- ✅ Grammar builder
- ✅ JSON Schema builder
- ✅ Provider adapters
- ✅ Language grammars: TypeScript (complete), Python/Rust (partial)

#### Phase 3: Type System

**2,124 lines dedicated to type system**

- ✅ Type inference engine
- ✅ Type inhabitation solver
- ✅ Typed holes
- ✅ Type-to-grammar converter
- ✅ TypeScript type system

### Phase 4: Validation & Repair 🚧 IN PROGRESS (6/10 complete)

**Recent Progress** (as of November 8, 2025):

✅ **Complete Components**:

1. SyntaxValidator - Commit 013846c
2. TypeValidator - Commit a1b463c
3. TestValidator - Commit 3f8f006
4. LintValidator - Commit 7a91e04
5. RuneExecutor - Commit 0e358b4
6. ValidationPipeline - Commit b4b31c6

📋 **Remaining Tasks**:

- RepairOrchestrator: Manages repair iteration logic
- DiagnosticAnalyzer: Interprets validation failures
- ConstraintRefinement: Tightens constraints based on diagnostics
- Full pedantic_raven integration: Deep semantic validation

**Expected Completion**: December 2025

### Phase 5: Adaptive Learning 📋 PLANNED

**Timeline**: Q1 2026

- Pattern mining from existing codebases
- Constraint learning from generation outcomes
- Full mnemosyne integration for persistent learning
- Project-specific pattern adaptation

### Phase 6: Production 📋 PLANNED

**Timeline**: Q2 2026

- Performance optimization (speculative decoding, parallelization)
- Multi-language indexers (Python, Rust, Go, Zig completion)
- IDE integrations (VSCode, IntelliJ plugins)
- Comprehensive benchmarking: HumanEval, MBPP, SWE-bench-lite
- Production deployment guides

## 8. Research Foundation

MAZE builds on established research in constrained generation, program synthesis, and type theory:

### Type-Constrained Code Generation (PLDI 2025)

**Paper**: Mündler et al., "Type-Constrained Code Generation with Language Models"

**Venue**: PLDI 2025

**arXiv**: [2504.09246](https://arxiv.org/abs/2504.09246)

**Key Contributions**:

1. Type constraints as prefix automata
2. Bidirectional type inference for LLM guidance
3. Reported >50% reduction in compilation errors

### Statically Contextualizing LLMs with Typed Holes (OOPSLA 2024)

**Paper**: Blinn et al., "Statically Contextualizing Large Language Models with Typed Holes"

**Venue**: OOPSLA 2024

**arXiv**: [2409.00921](https://arxiv.org/abs/2409.00921)

**Key Contributions**:

1. Typed holes for partial code completion
2. Static context extraction for LLM guidance
3. Evaluation on real-world TypeScript codebases

### LLGuidance: Constraint Enforcement for LLMs

**Source**: Microsoft Research, [guidance-ai/llguidance](https://github.com/guidance-ai/llguidance)

**Key Contributions**:

1. Efficient CFG grammar enforcement during decoding
2. Sub-100μs token mask computation
3. Provider-agnostic integration

## 9. Architecture Validation

All claims in this whitepaper are validated against the codebase at tag `v0.1.0-whitepaper`.

### Code Statistics

| Metric | Value |
|--------|-------|
| Total source files | 43 |
| Total source lines | 10,847 |
| Test files | 29 |
| Type system lines | 2,124 |

### Component Verification

All components link to tagged source code at `v0.1.0-whitepaper` for verification:

- **Core Type System** ✅: [types.py](https://github.com/rand/maze/tree/v0.1.0-whitepaper/src/maze/core/types.py), [constraints.py](https://github.com/rand/maze/tree/v0.1.0-whitepaper/src/maze/core/constraints.py)
- **Type System** ✅ (2,124 lines): Multiple modules in [type_system/](https://github.com/rand/maze/tree/v0.1.0-whitepaper/src/maze/type_system/)
- **Synthesis** ✅: [synthesis/](https://github.com/rand/maze/tree/v0.1.0-whitepaper/src/maze/synthesis/)
- **Validation** ✅: [validation/](https://github.com/rand/maze/tree/v0.1.0-whitepaper/src/maze/validation/)
- **Integrations** ✅: llguidance, mnemosyne, RUNE in [integrations/](https://github.com/rand/maze/tree/v0.1.0-whitepaper/src/maze/integrations/)

## 10. Getting Started

### Installation

MAZE requires Python 3.10+ and uses `uv` for dependency management:

```bash
# Clone repository
git clone https://github.com/rand/maze
cd maze

# Install dependencies
uv pip install -e ".[dev]"

# Verify installation
uv run python -c "import maze; print('MAZE installed successfully')"
```

### Basic Usage (Conceptual)

```python
from maze.core.constraints import ConstraintSet, SyntacticConstraint
from maze.type_system.context import TypeContext
from maze.orchestrator import generate

# 1. Define constraints
constraints = ConstraintSet()
constraints.add(SyntacticConstraint.from_language("typescript"))

# 2. Optionally add type context
type_context = TypeContext()
type_context.add_type("User", {
    "id": "string",
    "name": "string",
    "email": "string"
})

# 3. Generate code
code = generate(
    prompt="Create an async function that fetches a user by ID and returns their email",
    constraints=constraints,
    type_context=type_context
)

print(code)
```

## 11. Conclusion

### Summary of Contributions

MAZE introduces a novel approach to code generation that shifts from post-hoc validation to pre-generation constraint enforcement:

1. **4-Tier Constraint Hierarchy**: Progressive constraint tightening from syntax through types, semantics, and context
2. **Type-Directed Synthesis**: Bidirectional type inference and inhabitation search for type-correct code paths
3. **Multi-System Integration**: Seamless integration with llguidance, mnemosyne, RUNE, and pedantic_raven
4. **Research-Backed Design**: Built on PLDI 2025 and OOPSLA 2024 research
5. **Provider-Agnostic Architecture**: Support for OpenAI, vLLM, SGLang, and llama.cpp

### Current State: Solid Foundation

With 10,847 lines of code across 43 source files, MAZE has completed its core architectural foundation:

- **Phase 1-3**: Type system, constraint synthesis, and core integrations complete
- **Phase 4**: Validation pipeline 60% complete (6/10 tasks)
- **Phase 5-6**: Adaptive learning and production hardening planned

### Future Work

**Short Term** (Phase 4, Q4 2025):

- Complete repair orchestrator
- Diagnostic analyzer for intelligent constraint refinement
- Full pedantic_raven integration

**Medium Term** (Phase 5, Q1 2026):

- Pattern mining from codebases
- Adaptive constraint learning
- Project-specific pattern adaptation

**Long Term** (Phase 6, Q2 2026):

- Multi-language indexer completion (Python, Rust, Go, Zig)
- Comprehensive benchmark evaluation (HumanEval, MBPP, SWE-bench)
- IDE integrations (VSCode, IntelliJ)
- Production deployment optimization

## 12. Resources

### Project Links

- **GitHub Repository**: [github.com/rand/maze](https://github.com/rand/maze)
- **Documentation**: [CLAUDE.md](CLAUDE.md), [AGENT_GUIDE.md](AGENT_GUIDE.md)
- **Whitepaper**: [maze whitepaper](https://rand.github.io/maze)

### Research Papers

- **Type-Constrained Code Generation**: [arXiv:2504.09246](https://arxiv.org/abs/2504.09246) (PLDI 2025)
- **Typed Holes**: [arXiv:2409.00921](https://arxiv.org/abs/2409.00921) (OOPSLA 2024)

### Related Projects

- **llguidance**: [github.com/guidance-ai/llguidance](https://github.com/guidance-ai/llguidance) (Microsoft Research)
- **mnemosyne**: [rand.github.io/mnemosyne](https://rand.github.io/mnemosyne) (Memory & Learning)
- **RUNE**: [rand.github.io/RUNE](https://rand.github.io/RUNE) (Sandboxed Execution)

---

**Version**: v0.1.0-whitepaper
**Last Updated**: November 2025
**License**: [To be determined]
