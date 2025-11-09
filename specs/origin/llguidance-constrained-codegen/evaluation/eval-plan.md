# Evaluation plan

- Datasets: HumanEval(+fix), MBPP, repo‑local tasks with unit tests.
- Measure:
  - Compile success rate.
  - pass@1/3/10.
  - TTFT, TPOT; wall‑clock per task.
  - Masked‑token ratio; retries required.
- Compare engines: LLGuidance vs XGrammar vs Outlines on same grammar when possible.
- Test types:
  - JSON plans (tool calls).
  - Single‑function fills with typed holes (TS).
  - Multi‑file patches with imports.
- Report deltas from repair loop and constraint edits applied.
