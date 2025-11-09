# Architecture and component specs

## 0. Tech baseline
- Engine: **LLGuidance** as the grammar backend. Python orchestration via Guidance.
- Inference servers: OpenAI (Structured Outputs), vLLM (with --grammar-backend llguidance), SGLang, llama.cpp.
- Static analysis hooks:
  - Python: pyright or mypy JSON output.
  - TypeScript: tsserver / tsc `--pretty false --listFiles --incremental` plus language service protocol.
  - Rust: rust-analyzer `ssr` and `check` JSON.
  - Haskell: GHCi + hole fits (inspiration from OllamaHoles).

## 1. Context Indexer
- Detect languages; index symbols, signatures, types; extract API specs and JSON schemas from docstrings or Pydantic/TS types.
- Surface “constraints candidates”:
  - enums, literal types, shape types, numeric bounds, regexes, doc‑style “must/should” sentences.

### Outputs (canonical IR)
```json
{
  "files": [{"path":"src/foo.ts","lang":"ts"}],
  "symbols": [{"name":"createUser","type":"(p: Person) => Promise<User>"}],
  "schemas": [{"id":"Person","jsonSchema":{...}}],
  "style": {"indent":2,"quotes":"single","maxLen":100},
  "tests": [{"kind":"unit","cmd":"pnpm test -t user"}]
}
```

## 2. Constraint Synthesis
- **JSON Schema builder**: from Pydantic/TS types; for edit plans, tool calls, AST JSON.
- **CFG/Lark builder**: per‑language templates with `%json` inlines and regex lexing; supports fenced reasoning then structured output.
- **Type holes**:
  - TS: incremental type env; compute allowed productions for a hole’s type class and free vars; encode into grammar nonterminals.
  - Rust/Haskell: analogous; start with TS for practicality.

### Example: constrained function patch (TS)
Produces a grammar guaranteeing:
- file header unchanged except in marked region
- only valid imports
- function body matches a template and is well‑typed up to a conservative prefix check

## 3. Decode Orchestrator
- Provider adapters:
  - `openai_structured(schema)` for JSON outcomes.
  - `guidance_generate(grammar, prompt)` for CFG.
  - vLLM/SGLang/llama.cpp adapters with llguidance masks.
- Retries:
  - repair on compile/test failure by narrowing grammars or adding `%json` constraints inside CFG.
  - keep provenance and diffs.

## 4. Post‑checks
- Lint, format, compile, run unit tests in sandbox.
- Summarize diagnostics into constraint updates (regex forbids, enum tightenings, signature shims).

## 5. Caching & telemetry
- Cache grammars and schema coverage; keep per‑engine feature matrix.
- Emit structured logs: tokens masked ratio, time per mask, TTFT/TPOT.
