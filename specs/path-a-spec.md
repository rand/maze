# Path A: Provider Integration & Grammar Loading - Specification

**Status**: 📋 Planning (Phase 1: Prompt → Spec)
**Priority**: HIGH - Makes system functional for actual code generation
**Estimated Duration**: 1-2 days
**Dependencies**: Phase 6 complete ✅

## Executive Summary

Path A completes the critical gap between having a functional pipeline and actually generating real code. Currently, the pipeline returns placeholder code. This path wires up existing provider adapters to the pipeline and loads grammar templates for constraint enforcement.

## Problem Statement

Current limitations:
1. `Pipeline._generate_with_constraints()` returns placeholder code (line 381)
2. `Pipeline._synthesize_constraints()` returns empty grammar (lines 358-360)
3. Grammar not passed through repair flow (line 335)
4. No actual LLM calls happening

**Impact**: System is structurally complete but not functionally operational.

## Objectives

### 1. Wire Provider Adapters to Pipeline
**Goal**: Enable actual LLM code generation through existing adapters

**Current State**:
- Provider adapters exist: `src/maze/orchestrator/providers/`
- OpenAI, vLLM, SGLang, llama.cpp implementations ✅
- Pipeline has placeholder: `return f"// Generated code for: {prompt}..."`

**Needed**:
- Import and use provider adapters in pipeline
- Route requests based on `config.generation.provider`
- Pass grammar constraints to provider
- Handle API responses and errors

### 2. Load Grammar Templates
**Goal**: Apply syntactic constraints during generation

**Current State**:
- Grammar templates exist: `src/maze/synthesis/grammars/`
- GrammarBuilder exists but not used in pipeline
- `_synthesize_constraints()` returns empty string

**Needed**:
- Load language-specific grammar templates
- Build grammar with GrammarBuilder
- Embed type constraints in grammar (if enabled)
- Cache compiled grammars

### 3. Connect Grammar Through Repair Flow
**Goal**: Enable constraint refinement during repair

**Current State**:
- Repair gets empty grammar (line 335)
- RepairOrchestrator expects grammar for refinement

**Needed**:
- Store grammar from generation step
- Pass grammar to repair
- Enable constraint tightening

### 4. Provider Configuration & Error Handling
**Goal**: Robust provider interaction with fallbacks

**Needed**:
- API key validation
- Timeout handling
- Rate limiting
- Retry logic
- Error messages

## Scope

### In Scope
- OpenAI provider integration (primary)
- Grammar template loading for TypeScript
- Grammar caching
- Provider error handling
- Basic retry logic
- Update pipeline to use real generation
- Tests for provider integration

### Out of Scope
- Multi-provider orchestration (use config to select one)
- Advanced rate limiting strategies
- Provider-specific optimizations
- Non-TypeScript grammar templates (defer to Path B)

## Success Criteria

1. ✅ `maze generate "Create a function"` produces real TypeScript code
2. ✅ Grammar constraints applied during generation
3. ✅ Type constraints embedded in grammar (if enabled)
4. ✅ Provider errors handled gracefully
5. ✅ Repair receives grammar for refinement
6. ✅ End-to-end test: init → index → generate → validate → repair
7. ✅ Performance: <10s per prompt (already validated with placeholder)

## Risk Assessment

**Low Risk**:
- Provider adapters already implemented ✅
- Grammar templates already exist ✅
- Pipeline structure supports this ✅
- Minimal API changes needed

**Potential Issues**:
- API keys needed for testing (can mock)
- Provider API changes (use latest client libs)
- Grammar compilation errors (validate in tests)

## Performance Targets

- **Provider call**: <8s (depends on LLM)
- **Grammar loading**: <50ms (from cache: <1ms)
- **Total pipeline**: <10s ✅ (already validated)

## Next Steps

After spec approval:
1. Create full-spec.md with typed holes
2. Create plan.md with task ordering
3. Implement components
4. Test end-to-end
5. Update documentation
