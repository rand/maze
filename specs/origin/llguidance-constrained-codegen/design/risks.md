# Risks, gaps, decisions

- Coverage: Some engines lack full JSON Schema feature support. Keep a feature matrix and route per schema.
- Over‑constraint: Start loose; tighten on failure based on diagnostics. Keep a reproducible trail.
- Diffusion LLMs: Use semantic checks until CFG decoding for dLLMs is mainstream; research exists for CFG‑constrained diffusion decoding.
- Type enforcement: Type‑constrained decoding is non‑CFG; integrate per‑language type engines as side constraints at hole level; do not attempt full language typing via CFG.
