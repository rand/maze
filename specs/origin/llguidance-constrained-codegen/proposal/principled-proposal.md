# Principled proposal: Adaptive Constraint Builder (ACB) for Code Gen

## Thesis
Agentic coding systems become faster and more correct when they **compile explicit constraints** before they decode code. ACB turns messy inputs — prompts, specs, repos, files, traces — into **LLGuidance** grammars and JSON Schemas, optionally enriched with **type‑safety constraints** and **task‑local test or API contracts**, then runs constrained decoding. It also performs **hole‑driven generation**: it emits typed “holes” and fills them under constraints.

## Design goals
1. **Correctness first**: maximize compile rate and test pass@k.  
2. **Speed**: mask computation ≤ model forward pass; cache grammars.  
3. **Context fidelity**: constraints reflect local codebase types, APIs, and style.  
4. **Interoperability**: work with OpenAI Structured Outputs, vLLM, SGLang, llama.cpp, and Guidance Python.  
5. **Explainability**: every generation is accompanied by the exact grammar/schema and provenance.

## System architecture
```
Inputs (prompt, spec, repo, files, traces)
           │
           ▼
 ┌──────────────────────────┐
 │  Context Indexer         │  Static analysis + embeddings + symbol tables
 │  - lang detectors        │  (pyright/mypy, tsserver, rust-analyzer hooks)
 │  - API & types harvest   │
 └──────────┬───────────────┘
            │ Symbols & contracts
            ▼
 ┌──────────────────────────┐
 │ Constraint Synthesis     │  → JSON Schema, Regex, CFG/Lark
 │  - JSON schema builder   │  - Code CFG templates per lang
 │  - Style/linters (regex) │  - Typed-hole generators
 │  - Test stubs            │
 └──────────┬───────────────┘
            │ Grammars + Schemas
            ▼
 ┌──────────────────────────┐
 │ Decode Orchestrator      │  LLGuidance-backed constrained decoding
 │  - Provider adapters     │  (OpenAI Structured Outputs, vLLM, SGLang)
 │  - Cache + fast-forward  │
 │  - Retry/repair loops    │
 └──────────┬───────────────┘
            │ Code + traces
            ▼
 Post-checks (compile/typecheck/linters/tests) → auto-repair under constraints
```

## Constraint stack (when to use what)
- **JSON Schema**: tool calls, refactors that return structured edits, AST JSON, config files.  
- **Regex**: quick style gates, filename patterns, identifier forms.  
- **CFG/Lark in LLGuidance**: language skeletons, templated functions, multi‑file patches.  
- **Type‑constrained decoding**: for typed languages (TS, Rust, Haskell); enforce **well‑typed prefixes** (per Mündler et al. 2025).  
- **Oracle constraints**: unit tests, contract checks, API sim calls — used in repair loop, not at token mask time.

## Key techniques
- **Hole‑driven generation**: emit `/* HOLE: type Env -> Expr */` and fill with grammar + types. Works well with TS and Haskell; Python uses type hints via pyright for partial checks.
- **Schema-from-context**: convert Pydantic/TypeScript types to JSON Schema, then `%json` in LLGuidance Lark grammar.
- **Grammar caching**: hash(context, task) → grammar key. Warm cache before first token; reuse across attempts.
- **Fast-forward tokens**: leverage LLGuidance’s optimization to skip deterministic scaffolding.
- **Provider abstraction**: OpenAI Structured Outputs (JSON only), Guidance (full CFG), vLLM/SGLang/llama.cpp with llguidance enabled.

## Interfaces
- `POST /plan`: returns constraint plan with trace of sources.  
- `POST /generate`: takes plan or raw inputs; returns code + grammar used.  
- `POST /repair`: accepts failing diagnostics; updates constraints and re‑decodes.

## Evaluation
- Benchmarks: HumanEval(+fix), MBPP, SWE-bench-lite; add internal tasks.  
- Metrics: compile rate, pass@1/3/10, TTFT, TPOT, wall‑clock, % constrained tokens, retries.  
- Ablations: JSON‑only vs CFG vs CFG+types; llguidance vs XGrammar vs Outlines on identical tasks.

## Risks and mitigations
- **Over‑constraint** → fallback to looser grammar; show delta.  
- **Coverage gaps** in engines → detect feature, route engine accordingly.  
- **Diffusion LLMs** (DiffuCoder) → use semantic post‑checks until CFG decoding for dLLMs matures.
