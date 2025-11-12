"""Modal deployment for Maze with vLLM + llguidance + Qwen2.5-Coder-32B.

This deploys a production-ready inference server with:
- Qwen2.5-Coder-32B-Instruct for code generation
- vLLM for fast inference
- llguidance for grammar-constrained generation
- FastAPI for HTTP endpoints

Deployment:
    modal deploy deployment/modal/modal_app.py

Usage:
    POST https://<user>--maze-inference-generate.modal.run
    {
        "prompt": "def add(a: int, b: int) -> int:",
        "grammar": "?start: function_def...",
        "max_tokens": 512,
        "temperature": 0.7
    }
"""

import modal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# Create Modal app
app = modal.App("maze-inference")

# Configure persistent volume for model caching
volume = modal.Volume.from_name("maze-model-cache", create_if_missing=True)

# Build custom image with vLLM and llguidance
image = (
    modal.Image.debian_slim(python_version="3.11")
    # System dependencies for building
    .apt_install(
        "git",
        "build-essential",
        "wget",
        "curl",
    )
    # vLLM with all dependencies
    .uv_pip_install(
        "vllm==0.8.5",
        "torch==2.6.0",
        "transformers==4.47.1",
        "fastapi==0.115.0",
        "pydantic==2.10.0",
    )
    # llguidance - clone and install from source
    .run_commands(
        "cd /tmp && git clone https://github.com/guidance-ai/llguidance.git",
        "cd /tmp/llguidance && cargo build --release --manifest-path parser/Cargo.toml",
        "cd /tmp/llguidance/python && pip install -e .",
    )
    # Environment configuration
    .env({
        "HF_HOME": "/cache/huggingface",
        "VLLM_CACHE": "/cache/vllm",
        "TRANSFORMERS_CACHE": "/cache/transformers",
        # Disable unnecessary warnings
        "TOKENIZERS_PARALLELISM": "false",
    })
)

# FastAPI app for HTTP endpoints
web_app = FastAPI(
    title="Maze Inference API",
    description="Grammar-constrained code generation with Qwen2.5-Coder-32B",
    version="1.0.0",
)


class GenerateRequest(BaseModel):
    """Request for code generation."""
    
    prompt: str = Field(..., description="Code generation prompt")
    grammar: Optional[str] = Field(None, description="Lark grammar for constraints")
    language: str = Field("python", description="Target language")
    max_tokens: int = Field(2048, ge=1, le=8192, description="Maximum tokens")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")


class GenerateResponse(BaseModel):
    """Response from code generation."""
    
    success: bool
    code: str
    metadata: dict


@app.cls(
    gpu="l40s",  # 48GB VRAM
    image=image,
    timeout=3600,  # 1 hour max
    container_idle_timeout=300,  # 5 minutes idle
    volumes={"/cache": volume},  # Persistent model cache
    secrets=[modal.Secret.from_name("huggingface-secret")],
    # Keep 1 container warm for low latency
    keep_warm=1,
)
class MazeInferenceServer:
    """vLLM inference server with llguidance for grammar-constrained generation."""

    @modal.enter()
    def load_model(self):
        """Initialize vLLM with Qwen2.5-Coder-32B and llguidance."""
        from vllm import LLM
        import torch
        
        print("=" * 60)
        print("Loading Qwen2.5-Coder-32B-Instruct with llguidance...")
        print("=" * 60)
        
        # Check GPU
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        
        # Initialize vLLM with llguidance backend
        self.llm = LLM(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            tensor_parallel_size=1,  # Single GPU
            gpu_memory_utilization=0.90,  # Use 90% of VRAM
            max_model_len=8192,  # Context length (balance speed vs capability)
            dtype="bfloat16",  # BF16 for quality
            trust_remote_code=True,
            download_dir="/cache/models",  # Persistent storage
            # Enable llguidance for grammar constraints
            guided_decoding_backend="llguidance",
        )
        
        print("✅ Model loaded successfully")
        
        # Report memory usage
        allocated = torch.cuda.memory_allocated() / 1e9
        reserved = torch.cuda.memory_reserved() / 1e9
        print(f"Memory allocated: {allocated:.2f} GB")
        print(f"Memory reserved: {reserved:.2f} GB")
        print(f"Headroom: {48 - reserved:.2f} GB")
        print("=" * 60)

    @modal.method()
    def generate(
        self,
        prompt: str,
        grammar: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> dict:
        """Generate code with optional grammar constraints.

        Args:
            prompt: Code generation prompt
            grammar: Optional Lark grammar for constraints
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated code and metadata
        """
        from vllm import SamplingParams
        import time
        
        start = time.time()
        
        # Configure sampling parameters
        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
            repetition_penalty=1.05,
        )
        
        # Add grammar constraint if provided
        if grammar:
            # llguidance integration in vLLM
            # Grammar should be in Lark format with %llguidance directive
            grammar_with_directive = f"%llguidance {{\n{grammar}\n}}"
            sampling_params.guided_grammar = grammar_with_directive
        
        # Generate with vLLM
        try:
            outputs = self.llm.generate([prompt], sampling_params)
            
            generated_text = outputs[0].outputs[0].text
            tokens_generated = len(outputs[0].outputs[0].token_ids)
            finish_reason = outputs[0].outputs[0].finish_reason
            
            duration = time.time() - start
            
            return {
                "success": True,
                "text": generated_text,
                "tokens_generated": tokens_generated,
                "duration_seconds": duration,
                "finish_reason": finish_reason,
                "grammar_applied": grammar is not None,
            }
        
        except Exception as e:
            return {
                "success": False,
                "text": f"// Generation failed: {str(e)}",
                "tokens_generated": 0,
                "duration_seconds": time.time() - start,
                "finish_reason": "error",
                "error": str(e),
            }

    @modal.method()
    def generate_batch(
        self,
        prompts: list[str],
        grammars: Optional[list[str]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> list[dict]:
        """Generate multiple codes in batch.

        Args:
            prompts: List of prompts
            grammars: Optional list of grammars (parallel to prompts)
            max_tokens: Maximum tokens per generation
            temperature: Sampling temperature

        Returns:
            List of generation results
        """
        from vllm import SamplingParams
        
        # Create sampling params for each prompt
        sampling_params_list = []
        
        for i, prompt in enumerate(prompts):
            params = SamplingParams(
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.95,
            )
            
            # Add grammar if provided
            if grammars and i < len(grammars) and grammars[i]:
                grammar_with_directive = f"%llguidance {{\n{grammars[i]}\n}}"
                params.guided_grammar = grammar_with_directive
            
            sampling_params_list.append(params)
        
        # Batch generate
        outputs = self.llm.generate(prompts, sampling_params_list)
        
        return [
            {
                "success": True,
                "text": output.outputs[0].text,
                "tokens_generated": len(output.outputs[0].token_ids),
            }
            for output in outputs
        ]

    @modal.web_endpoint(method="POST")
    def generate_endpoint(self, request: GenerateRequest) -> GenerateResponse:
        """HTTP endpoint for code generation.

        POST /generate
        Body: GenerateRequest JSON
        Returns: GenerateResponse JSON
        """
        result = self.generate(
            prompt=request.prompt,
            grammar=request.grammar,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Generation failed")
            )
        
        return GenerateResponse(
            success=result["success"],
            code=result["text"],
            metadata={
                "tokens_generated": result["tokens_generated"],
                "duration_seconds": result["duration_seconds"],
                "finish_reason": result["finish_reason"],
                "grammar_applied": result["grammar_applied"],
                "language": request.language,
            }
        )

    @modal.asgi_app()
    def fastapi_app(self):
        """Mount FastAPI app with health check and OpenAPI docs."""
        
        @web_app.get("/health")
        def health():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "model": "Qwen2.5-Coder-32B-Instruct",
                "backend": "vLLM + llguidance",
                "gpu": "L40S",
            }
        
        @web_app.post("/generate", response_model=GenerateResponse)
        def generate(request: GenerateRequest):
            """Generate code with optional grammar constraints."""
            return self.generate_endpoint(request)
        
        @web_app.get("/")
        def root():
            """Root endpoint with API info."""
            return {
                "service": "Maze Inference API",
                "model": "Qwen2.5-Coder-32B-Instruct",
                "features": [
                    "Grammar-constrained generation",
                    "5 languages supported",
                    "llguidance integration",
                ],
                "endpoints": {
                    "generate": "POST /generate",
                    "health": "GET /health",
                    "docs": "GET /docs",
                }
            }
        
        return web_app


# Local testing entrypoint
@app.local_entrypoint()
def test():
    """Test the deployment locally."""
    server = MazeInferenceServer()
    
    print("\n" + "=" * 60)
    print("Testing Maze Inference Server")
    print("=" * 60)
    
    # Test 1: Simple generation
    print("\nTest 1: Simple Python function generation")
    result = server.generate.remote(
        prompt="def add(a: int, b: int) -> int:",
        max_tokens=256,
    )
    
    print(f"Success: {result['success']}")
    print(f"Tokens: {result['tokens_generated']}")
    print(f"Duration: {result['duration_seconds']:.2f}s")
    print(f"Code:\n{result['text'][:200]}...")
    
    # Test 2: With grammar constraint
    print("\n" + "-" * 60)
    print("Test 2: TypeScript with grammar constraint")
    
    # Simple TypeScript grammar
    ts_grammar = """
    ?start: function_decl
    function_decl: "function" IDENT "(" params? ")" return_type? block
    params: IDENT ("," IDENT)*
    return_type: ":" IDENT
    block: "{" statement* "}"
    statement: "return" IDENT ";"
    IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
    %ignore /\\s+/
    """
    
    result = server.generate.remote(
        prompt="function add(a, b)",
        grammar=ts_grammar,
        max_tokens=128,
    )
    
    print(f"Success: {result['success']}")
    print(f"Grammar applied: {result['grammar_applied']}")
    print(f"Code:\n{result['text'][:200]}...")
    
    print("\n" + "=" * 60)
    print("✅ Tests complete!")
    print("=" * 60)
