# Coding agent super‑prompt: build the Adaptive Constraint Builder

You are an elite engineer. Implement the **Adaptive Constraint Builder (ACB)** that compiles constraints from repo context and runs **LLGuidance** constrained decoding for code generation.

## Objectives
- Ingest prompts/specs plus repo context; synthesize JSON Schemas, Lark grammars, and typed‑hole stubs.
- Route decoding through LLGuidance (CFG) or provider JSON Schema modes.
- Post‑check: compile, lint, run tests; if failing, **tighten or relax constraints** and retry.
- Return code and the exact constraints used, with provenance.

## Deliverables
- Python package `acb` with modules:
  - `acb/indexer` — language detection; pyright/tsserver hooks; schema harvesters.
  - `acb/constraints` — builders for JSON Schema, regex, Lark CFG; typed‑hole planners.
  - `acb/infer` — adapters: Guidance, OpenAI Structured Outputs, vLLM/SGLang/llama.cpp.
  - `acb/plan` — planner that chooses strategy per task.
  - `acb/repair` — convert diagnostics to constraint edits and re‑decode.
  - `cli` — `acb plan`, `acb generate`, `acb repair`.
- Tests for HumanEval‑style tasks plus repo‑local tasks.
- Example grammars in `examples/` and perf counters in logs.

## Hard requirements
- Use LLGuidance for CFG decoding. Support embedding `%json { … }` blocks.
- Cache grammars keyed by content hash. Pre‑warm before first token.
- Implement **hole‑driven generation** for TypeScript first. Emit `/*__HOLE_name__*/` then fill with grammar constrained by the hole’s type.
- Provider matrix with health‑checks: OpenAI SO, Guidance+llama.cpp, vLLM, SGLang.
- Telemetry: TTFT, TPOT, masked‑token ratio, success/failure reason.

## Implementation notes
- JSON schema builder: derive from TS/pyright types; allow enums, literals, min/max, regex patterns.
- Lark grammar: parameterize language skeletons. Include fenced `<think>` then structured section to preserve model reasoning without polluting outputs.
- Post‑checks call language toolchains non‑interactively; capture diags; map to constraint edits.
- Add ablation flags: `--no-types`, `--json-only`, `--engine=xgrammar` for comparisons.

## Milestones
1) MVP: JSON schemas + simple CFG for TS functions; OpenAI SO + Guidance backends.  
2) Typed‑holes for TS; repair loop.  
3) Multi‑file patches; Rust/Python support; benchmark harness.  
4) Performance: batch decoding; grammar cache; fast‑forward tokens.

## Acceptance tests
- 95% compile rate on internal TS tasks; +≥3pp pass@1 vs unconstrained baseline; TTFT within 10% of unconstrained on vLLM for small batch.
