# System dependencies
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    echo "Installing dependencies for macOS..."
    brew install libnss libnspr atk at-spi2-atk cups xkbcommon cairo pango
elif [ "$(uname)" == "Linux" ]; then
    # Linux
    echo "Installing dependencies for Linux..."
    apt-get update
    apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
        libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
        libpango-1.0-0 libcairo2 libasound2 build-essential
else
    echo "Unsupported operating system"
    exit 1
fi

# Clean existing installations
pip uninstall -y torch torchvision torchaudio flash-attn
pip cache purge

# Check CUDA availability and install PyTorch accordingly
if command -v nvidia-smi &> /dev/null; then
    # CUDA is available
    echo "CUDA detected - installing PyTorch with CUDA support"
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    
    # Install flash-attention related packages
    pip install --no-cache-dir packaging ninja wheel
    TORCH_CUDA_ARCH_LIST="8.0" pip install --no-cache-dir flash-attn --no-build-isolation
    pip install flashinfer -i https://flashinfer.ai/whl/cu124/torch2.4
else
    # CPU only
    echo "No CUDA detected - installing PyTorch CPU version"
    pip install --no-cache-dir torch torchvision torchaudio
    echo "Skipping flash-attention and flashinfer (CUDA-only packages)"
fi

# Core ML libraries
pip install --no-cache-dir transformers accelerate bitsandbytes

# Additional ML packages
pip install --no-cache-dir trl anthropic groq openai huggingface_hub \
    datasets peft deepspeed sentence_transformers nest_asyncio orjson sglang python-multipart hydra-core --upgrade

# VLLM and Jupyter
pip install --no-cache-dir vllm jupyterlab

# Install pyreft
pip install git+https://github.com/stanfordnlp/pyreft.git

pip install --force-reinstall "numpy<2.0"