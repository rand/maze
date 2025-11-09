# Annotated bibliography (validated links)

- LLGuidance repo and feature list. Integrations: OpenAI Structured Outputs, llama.cpp, Chromium, SGLang, vLLM; supports JSON Schema, regex, and Lark‑like CFG; ~50 μs/mask typical with slicer optimization.  
  Link: https://github.com/guidance-ai/llguidance

- LLGuidance technical blog: algorithms, token‑trie, lexer/parser split, slicer; sample `%json` in Lark.  
  Link: https://guidance-ai.github.io/llguidance/llg-go-brrr

- JSONSchemaBench paper and benchmark comparing Guidance, Outlines, XGrammar, Llama.cpp, OpenAI, Gemini; finds constrained decoding can speed generation and improve quality.  
  Link: https://arxiv.org/abs/2501.10868

- Statically Contextualizing LLMs with Typed Holes (Blinn et al., OOPSLA 2024): typed‑hole scaffolding to inject **static context** into prompts and completions.  
  Link: https://arxiv.org/abs/2409.00921

- Type‑Constrained Code Generation (Mündler et al., 2025; PLDI/OOPSLA lineage): introduces prefix automata + type‑inference search to enforce well‑typedness for TypeScript; large drops in compile errors, boosts functional correctness.  
  Link: https://arxiv.org/abs/2504.09246  
  Code: https://github.com/eth-sri/type-constrained-code-generation

- OllamaHoles (Tritlo): GHC plugin that uses LLMs to fill typed holes, with guidance and doc‑lookups — pragmatic pattern for hole‑driven workflows.  
  Link: https://github.com/Tritlo/OllamaHoles

- XGrammar: alternative engine with PDA batching and pre‑computation; sometimes fast but sensitive; useful comparative point.  
  Link: https://github.com/mlc-ai/xgrammar  Docs: https://xgrammar.mlc.ai/docs/

- Outlines: Python library for structured outputs (Pydantic, regex, CFG); useful as a baseline.  
  Link: https://github.com/dottxt-ai/outlines

- DiffuCoder‑7B‑cpGRPO (Apple): diffusion‑based coding LLM; coupled‑GRPO RL improves +4.4% EvalPlus and reduces AR bias; constrained decoding for diffusion models is emerging.  
  Model: https://huggingface.co/apple/DiffuCoder-7B-cpGRPO  
  Paper: https://arxiv.org/abs/2506.20639  
  Code:  https://github.com/apple/ml-diffucoder
