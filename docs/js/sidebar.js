// MAZE-specific sidebar comments
// Load this BEFORE sidebar-base.js

(function() {
    // Set theme key for MAZE
    window.THEME_KEY = 'maze-theme';

    // Detect which page we're on
    const path = window.location.pathname;
    const isWhitepaper = path.includes('whitepaper');

    if (isWhitepaper) {
        // Whitepaper page comments
        window.SIDEBAR_COMMENTS = {
            'abstract': '// Constrain before decoding: 50% fewer type errors',
            'table-of-contents': '// Your guide through constraint-driven generation',
            '1-introduction': '// LLMs generate plausible code, not correct code',
            '2-problem-statement': '// Unconstrained generation → 3-5 repair iterations',
            '3-architecture-overview': '// 5 stages: Index → Synthesize → Decode → Validate → Repair',
            '4-4-tier-constraint-system': '// Syntax → Types → Semantics → Context',
            '5-type-directed-synthesis': '// Inhabitation search: User → string paths',
            '6-integration-ecosystem': '// llguidance + mnemosyne + RUNE + pedantic_raven',
            '7-implementation-status-and-roadmap': '// 10,847 lines • Phases 1-3 complete • Phase 4 60%',
            '8-research-foundation': '// PLDI 2025 + OOPSLA 2024 + Microsoft Research',
            '9-architecture-validation': '// Every claim tagged to v0.1.0-whitepaper',
            '10-getting-started': '// uv pip install -e ".[dev]"',
            '11-conclusion': '// Pre-generation constraints > post-hoc validation',
            '12-resources': '// Papers, projects, and the rabbit hole awaits'
        };

        window.SIDEBAR_SUBSECTIONS = {
            // Introduction
            'The Code Generation Challenge': '// Plausible ≠ Correct: The LLM code dilemma',
            'MAZE\'s Paradigm Shift': '// Build constraints → Generate (constrained) → Done',
            'Architecture Foundation': '// 4-tier constraints + Type synthesis + Multi-system',

            // Problem Statement
            'Unconstrained LLM Generation Failures': '// Missing types, null checks, error handling',
            'The Cost of Post-Hoc Validation': '// 3-5 iterations burning API calls and time',
            'Type Errors in Generated Code': '// 50%+ functions have type errors (PLDI 2025)',

            // Architecture Overview
            'Stage 1: Context Indexer': '// TypeScript parser extracts types, functions, style',
            'Stage 2: Constraint Synthesis': '// CFG grammars + type constraints + JSON Schema',
            'Stage 3: Decode Orchestrator': '// llguidance enforces constraints <100μs/token',
            'Stage 4: Post-Validation': '// Syntax, types, tests, lints in parallel',
            'Stage 5: Repair Loop': '// Analyze failures → Refine constraints → Retry',
            'Integration Flow': '// llguidance + mnemosyne + RUNE + pedantic_raven',

            // 4-Tier Constraint System
            'Tier 1: Syntactic Constraints': '// CFG grammars ensure parse-ability',
            'Tier 2: Type Constraints': '// Inhabitation search for type-correct paths',
            'Tier 3: Semantic Constraints': '// Test cases validate behavior correctness',
            'Tier 4: Contextual Constraints': '// Project patterns learned from codebase',
            'Constraint Composition': '// Hierarchical narrowing to conformant code',

            // Type-Directed Synthesis
            'Bidirectional Type Inference': '// Bottom-up synthesis + top-down checking',
            'Type Inhabitation Solver': '// Memoized, depth-limited, ranked paths',
            'Typed Hole Filling': '// Partial code with __HOLE__ markers',

            // Integration Ecosystem
            'llguidance: Constraint Enforcement': '// 50μs mask computation, <50ms compilation',
            'mnemosyne: Persistent Memory': '// Learn patterns across sessions',
            'RUNE: Sandboxed Execution': '// Safe test validation with resource limits',
            'pedantic_raven: Quality Enforcement': '// Deep semantic validation (planned)',

            // Implementation Status
            'Current Status: Active Development': '// Phase 4: 6/10 tasks complete',
            'Phase 1-3: Core System ✅ COMPLETE': '// 10,847 lines across 43 files',
            'Phase 1: Foundation': '// Type system, constraints, llguidance, tests',
            'Phase 2: Syntactic Synthesis': '// Grammar + JSON Schema builders + adapters',
            'Phase 3: Type System': '// 2,124 lines: inference + inhabitation + holes',
            'Phase 4: Validation & Repair 🚧 IN PROGRESS (6/10 complete)': '// Validators done, repair orchestrator pending',
            'Phase 5: Adaptive Learning 📋 PLANNED': '// Pattern mining + constraint learning (Q1 2026)',
            'Phase 6: Production 📋 PLANNED': '// Performance, multi-language, IDE plugins (Q2 2026)',

            // Research Foundation
            'Type-Constrained Code Generation': '// PLDI 2025: 50% error reduction via constraints',
            'Statically Contextualizing LLMs': '// OOPSLA 2024: Typed holes for completion',
            'llguidance: Constraint Enforcement for LLMs': '// Microsoft Research: sub-100μs CFG',

            // Validation
            'Code Statistics': '// 10,847 source lines • 29 test files',
            'Component Verification': '// All claims link to tagged source code',

            // Getting Started
            'Installation': '// uv pip install -e ".[dev]"',
            'Basic Usage': '// generate(prompt, constraints, type_context)',

            // Conclusion
            'Summary of Contributions': '// 4-tier constraints + type synthesis + research-backed',
            'Current State: Solid Foundation': '// Phases 1-3 done, Phase 4 60%, Phase 5-6 planned',
            'Future Work': '// Repair orchestrator → Pattern mining → Production'
        };

        window.SIDEBAR_DEFAULT = '// Constraint-driven LLM code generation';
    } else {
        // Index page comments
        window.SIDEBAR_COMMENTS = {
            'abstract': '// Compile constraints before decoding, not after',
            'the-paradigm-shift': '// Because "just fix it later" is technical debt',
            'architecture': '// 5-stage pipeline: Index → Synthesize → Orchestrate → Validate → Repair',
            '4-tier-constraint-system': '// 4 tiers: Syntax → Types → Semantics → Context',
            'integration-ecosystem': '// Standing on the shoulders of giants (and Microsoft Research)',
            'implementation-status': '// Phase 3/6 complete • 60% validation coverage',
            'research-foundation': '// PLDI 2025 • OOPSLA 2024 • llguidance',
            'architecture-validation': '// 12K lines of Rust • Property tests FTW',
            'getting-started': '// cargo install --git ...'
        };

        window.SIDEBAR_SUBSECTIONS = {
            'Traditional Approach: Generate, Then Fix': '// Hope-driven development: generate → pray → patch',
            'MAZE Approach: Constrain, Then Generate': '// Constraint-driven: synthesize → decode → validate',
            'Stage 1: Context Indexer': '// Parse the world before constraining it',
            'Stage 2: Constraint Synthesis': '// CFG + types + tests = formal guarantees',
            'Stage 3: Decode Orchestrator': '// llguidance integration: <100μs constraint checks',
            'Stage 4: Post-Validation': '// Because compile-time constraints miss runtime state',
            'Stage 5: Repair Loop': '// When things go wrong, iterate (not panic)',
            'Tier 1: Syntactic Constraints': '// CFG: the bouncer at the syntax nightclub',
            'Tier 2: Type Constraints': '// Inhabitation search: find me a value of this type',
            'Tier 3: Semantic Constraints': '// Unit tests as executable specifications',
            'Tier 4: Contextual Constraints': '// Code review rules: no hardcoded credentials',
            'llguidance (Microsoft Research)': '// Fast CFG constraints for LLM decoding',
            'mnemosyne (Persistent Memory)': '// Remember what worked last time',
            'RUNE (Sandboxed Execution)': '// Run untrusted code, sleep soundly',
            'pedantic_raven (Quality Enforcement)': '// Semantic analysis: because linters lie',
            'Phases 1-3: Core System (Complete)': '// Context + constraints + orchestration ✓',
            'Phase 4: Validation and Repair (60 percent complete)': '// Property tests + repair loop in progress',
            'Phase 5: Adaptive Learning (Planned)': '// Learn from failures, adapt constraints',
            'Phase 6: Production (Planned)': '// Zero-downtime deployment, because YOLO is not a strategy',
            'Type-Constrained Code Generation (PLDI 2025)': '// Academic street cred: peer-reviewed',
            'Statically Contextualizing LLMs with Typed Holes (OOPSLA 2024)': '// More academic street cred',
            'LLGuidance (Microsoft Research)': '// The engine that makes sub-100μs possible',
            'Code Statistics': '// 12K lines Rust • 8K lines tests • 60% coverage',
            'Component Verification': '// Every claim tagged to source code'
        };

        window.SIDEBAR_DEFAULT = '// Constraint-driven LLM code generation';
    }
})();
