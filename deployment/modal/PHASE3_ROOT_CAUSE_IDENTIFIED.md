# Phase 1-3 Complete: Root Cause Identified

**Date**: 2025-11-12  
**Status**: ✅ ROOT CAUSE FOUND

---

## The Problem

**vLLM 0.11.0 expects GBNF grammar format, but Maze uses Lark grammar format.**

### Evidence

Error from vLLM:
```
Failed to convert the grammar from GBNF to Lark: Expected name at line 2, '\n' ^ '?start: function_def'
```

###  Grammar Format Comparison

**Lark format (what Maze uses)**:
```lark
?start: function_def
function_def: "def" IDENT "(" parameters? ")" ":" suite
IDENT: /[a-z_][a-z0-9_]*/
```

**GBNF format (what vLLM 0.11.0 expects)**:
```gbnf
root ::= function_def
function_def ::= "def " IDENT "(" parameters? ")" ":" suite
IDENT ::= [a-z_][a-z0-9_]*
```

**Key differences**:
1. Rule syntax: `:` (Lark) vs `::=` (GBNF)
2. Start rule: `?start:` (Lark) vs `root ::=` (GBNF)
3. Regex syntax: `/pattern/` (Lark) vs `[pattern]` (GBNF)
4. Optional marker: `?` prefix (Lark) vs `?` suffix (GBNF)

---

## What We Discovered

### Phase 1: Diagnostic
- ✅ Grammar IS being sent to Modal endpoint
- ✅ Grammar reaches vLLM
- ✅ `StructuredOutputsParams` API is correct for vLLM 0.11.0
- ✅ llguidance version is correct (0.7.11-0.7.99)

### Phase 2: API Verification
- ✅ vLLM 0.11.0 DOES have `StructuredOutputsParams`
- ✅ Correct usage: `SamplingParams(structured_outputs=StructuredOutputsParams(grammar=...))`
- ✅ Do NOT set `structured_outputs_config` on LLM init
- ✅ Do NOT use deprecated `guided_grammar` parameter

### Phase 3: Grammar Format Issue
- ❌ vLLM 0.11.0's llguidance expects **GBNF format**
- ❌ Maze provides **Lark format**
- ❌ No automatic conversion in vLLM 0.11.0

---

## Solution Options

### Option 1: Convert Lark → GBNF (Recommended)
**Implement grammar converter in Maze**

```python
# src/maze/synthesis/grammar_converter.py
def lark_to_gbnf(lark_grammar: str) -> str:
    """Convert Lark grammar to GBNF format for vLLM."""
    # Replace rule syntax
    gbnf = lark_grammar.replace(": ", " ::= ")
    
    # Replace start rule
    gbnf = re.sub(r'\?start:', 'root ::=', gbnf)
    
    # Convert regex patterns
    gbnf = re.sub(r'/([^/]+)/', r'[\1]', gbnf)
    
    # Other conversions...
    return gbnf
```

**Pros**:
- Works with vLLM 0.11.0
- Keeps Maze's native Lark grammars
- One-time conversion per grammar

**Cons**:
- Need to implement converter
- May not handle all Lark features
- Adds complexity

### Option 2: Use vLLM with Native Lark Support
**Upgrade to vLLM version with Lark support**

The Librarian mentioned newer vLLM (with llguidance >=1.3.0) supports Lark directly.

**Pros**:
- No grammar conversion needed
- Direct Lark support

**Cons**:
- Requires newer vLLM (not released as 0.11.0)
- May need to use main branch
- Less stable

### Option 3: Store Grammars in GBNF Format
**Change Maze to use GBNF natively**

```python
# src/maze/synthesis/grammars/python.py
PYTHON_FUNCTION_GBNF = """
root ::= function_def
function_def ::= "def " IDENT "(" parameters? ")" ":" suite
...
"""
```

**Pros**:
- Direct compatibility with vLLM 0.11.0
- No runtime conversion

**Cons**:
- Breaks existing Maze grammars
- GBNF is less expressive than Lark
- Major refactor required

---

## Recommended Approach

**Implement Option 1: Lark → GBNF Converter**

### Implementation Plan

1. **Create converter module** (`src/maze/synthesis/grammar_converter.py`)
   - Implement `lark_to_gbnf()` function
   - Handle common Lark patterns
   - Add tests

2. **Update Modal adapter** (`src/maze/orchestrator/providers/modal.py`)
   - Import converter
   - Convert grammar before sending to vLLM
   - Cache converted grammars

3. **Test conversion**
   - Test with Python grammar
   - Test with TypeScript grammar
   - Test with all 5 languages

4. **Validate constraints work**
   - Run constraint_enforcement tests
   - Verify 95%+ syntax validity
   - Measure improvement vs unconstrained

---

## Next Steps

1. **Implement Lark → GBNF converter** (1 hour)
2. **Test with simple grammar** (30 min)
3. **Test with full Python grammar** (30 min)
4. **Run full validation suite** (1 hour)
5. **Document findings** (30 min)

**Total**: 3-4 hours to working constraints

---

## Key Learnings

1. **Always check grammar format compatibility**
   - Different backends expect different formats
   - GBNF, Lark, EBNF, JSON Schema are NOT interchangeable

2. **Read the actual examples**
   - vLLM examples showed GBNF format
   - We missed this initially

3. **Error messages are critical**
   - "Failed to convert grammar from GBNF to Lark" was the smoking gun
   - Should have caught this earlier

4. **Test with minimal cases first**
   - Would have caught format issue faster
   - Don't test complex grammars until simple ones work

---

## Status

**Phase 1-3**: ✅ COMPLETE  
**Root Cause**: ✅ IDENTIFIED  
**Solution**: Ready to implement  
**ETA to working constraints**: 3-4 hours

