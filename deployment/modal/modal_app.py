"""Modal deployment for Maze with vLLM 1.0 + llguidance + Qwen2.5-Coder-32B.

This deploys a production-ready inference server with:
- Qwen2.5-Coder-32B-Instruct for code generation
- vLLM 1.0 for fast inference
- llguidance for Lark grammar-constrained generation (NOT XGrammar)
- FastAPI for HTTP endpoints

CRITICAL: llguidance is required for Lark grammars (Maze's native format).
XGrammar only supports JSON Schema and is NOT sufficient for Maze's use case.

Deployment:
    ./deployment/modal/scripts/deploy.sh
    
    Or manually:
    modal deploy deployment/modal/modal_app.py

Usage:
    POST https://<user>--maze-inference-fastapi-app.modal.run/generate
    {
        "prompt": "def add(a: int, b: int) -> int:",
        "grammar": "?start: function_def\nfunction_def: ...",
        "language": "python",
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

# Build optimized image with vLLM 1.0 + llguidance for Lark grammar support
# Key: llguidance supports Lark grammars (Maze's native format)
# XGrammar only supports JSON Schema - NOT sufficient for Maze

# Pinned versions for reproducibility
VLLM_VERSION = "1.0.0"  # Latest stable with llguidance support
TRANSFORMERS_VERSION = "4.47.1"  # Compatible with vLLM 1.0
FASTAPI_VERSION = "0.115.12"

image = (
    # Use NVIDIA CUDA development image (required for llguidance + flashinfer JIT)
    # Includes Rust compiler needed for llguidance build
    modal.Image.from_registry(
        "nvidia/cuda:12.4.1-devel-ubuntu22.04",
        add_python="3.12"
    )
    # System dependencies including Rust for llguidance
    .apt_install(
        "git",
        "wget",
        "curl",
        "build-essential",  # C/C++ compilers
        "pkg-config",
        "libssl-dev",  # For Rust builds
    )
    # Install Rust (required for llguidance)
    .run_commands(
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
        "echo 'source $HOME/.cargo/env' >> $HOME/.bashrc",
    )
    # Core ML dependencies
    .uv_pip_install(
        f"vllm=={VLLM_VERSION}",
        f"transformers=={TRANSFORMERS_VERSION}",
        f"fastapi[standard]=={FASTAPI_VERSION}",
        "huggingface-hub>=0.20.0",
        "hf-transfer",
        "flashinfer-python",
    )
    # Build and install llguidance from source
    .run_commands(
        # Source Rust environment
        ". $HOME/.cargo/env",
        # Clone llguidance
        "cd /tmp && git clone https://github.com/guidance-ai/llguidance.git",
        # Build Rust parser
        "cd /tmp/llguidance/parser && cargo build --release",
        # Install Python bindings
        "cd /tmp/llguidance/python && pip install -e .",
        # Verify installation
        "python -c 'import llguidance; print(\"llguidance installed:\", llguidance.__version__)'",
    )
    # Environment configuration
    .env({
        # CUDA paths
        "CUDA_HOME": "/usr/local/cuda",
        "PATH": "/usr/local/cuda/bin:$HOME/.cargo/bin:${PATH}",
        "LD_LIBRARY_PATH": "/usr/local/cuda/lib64:/usr/local/cuda/lib",
        # Performance
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
        "TOKENIZERS_PARALLELISM": "false",
        # Cache
        "HF_HOME": "/cache/huggingface",
        "TRANSFORMERS_CACHE": "/cache/transformers",
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


# Environment-based configuration (lift-sys pattern)
MODAL_MODE = os.getenv("MODAL_MODE", "dev").lower()

if MODAL_MODE == "demo":
    SCALEDOWN_WINDOW = 600  # 10 min for presentations
    GPU_CONFIG = "l40s"  # 48GB, $1.20/hr
    print("🎬 DEMO MODE: 10 min scaledown, L40S GPU")
elif MODAL_MODE == "prod":
    SCALEDOWN_WINDOW = 300  # 5 min balanced
    GPU_CONFIG = "l40s"
    print("🚀 PROD MODE: 5 min scaledown, L40S GPU")
else:
    # Dev mode: aggressive scaledown for cost savings
    SCALEDOWN_WINDOW = 120  # 2 min aggressive
    GPU_CONFIG = "l40s"
    print("💻 DEV MODE: 2 min scaledown (cost-optimized)")

print(f"Scaledown: {SCALEDOWN_WINDOW}s")

@app.cls(
    gpu=GPU_CONFIG,  # L40S: 48GB VRAM, ~$1.20/hour
    image=image,
    timeout=3600,  # 1 hour max
    container_idle_timeout=SCALEDOWN_WINDOW,  # Environment-based
    volumes={
        "/cache": volume,  # Model cache
        "/root/.cache/vllm": modal.Volume.from_name("maze-torch-cache", create_if_missing=True),  # Torch compilation cache
    },
    secrets=[modal.Secret.from_name("huggingface-secret")],
    # No keep_warm - use scaledown for cost optimization (lift-sys pattern)
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
        
        # Initialize vLLM 1.0 with llguidance for Lark grammar support
        # CRITICAL: llguidance supports Lark grammars (Maze's format)
        # XGrammar only does JSON Schema (not sufficient for Maze)
        self.llm = LLM(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            revision="main",
            tensor_parallel_size=1,  # Single GPU
            gpu_memory_utilization=0.90,
            max_model_len=8192,  # Balance speed vs capability
            dtype="bfloat16",
            trust_remote_code=True,
            download_dir="/cache/models",
            # llguidance for Lark grammar constraints
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
            # llguidance supports Lark grammars directly
            # This is what Maze uses natively (TypeScript, Python, Rust grammars)
            sampling_params.guided_decoding_backend = "llguidance"
            sampling_params.guided_grammar = grammar
        
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
