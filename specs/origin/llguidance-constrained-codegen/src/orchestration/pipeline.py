from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Literal

@dataclass
class ConstraintPlan:
    language: str
    strategy: Literal["json","regex","cfg","cfg+types"]
    lark_grammar: Optional[str] = None
    json_schema: Optional[Dict[str, Any]] = None
    provenance: List[str] = None

class Orchestrator:
    def __init__(self, adapter):
        self.adapter = adapter

    def generate(self, prompt: str, plan: ConstraintPlan) -> str:
        if plan.strategy in ("cfg","cfg+types"):
            res = self.adapter.generate_with_lark(prompt, plan.lark_grammar)
            return res.text
        elif plan.strategy == "json":
            data = self.adapter.generate_with_json_schema(prompt, plan.json_schema)
            return data.get("diff","")
        else:
            # Fall back to unconstrained (not recommended)
            return "/* unconstrained output: please set a grammar */"
