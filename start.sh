#!/bin/bash
set -e

# Detect container runtime
if [ -n "$CONTAINER_RUNTIME" ]; then
    RUNTIME="$CONTAINER_RUNTIME"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
elif command -v docker &> /dev/null; then
    RUNTIME="docker"
else
    echo "Error: Neither podman nor docker found."
    exit 1
fi

# Detect Hardware
if command -v nvidia-smi &> /dev/null; then
    echo "Nvidia GPU detected."
    TARGET="nvidia"
    DOCKERFILE="Dockerfile.nvidia"
    IMAGE_NAME="epub2tts-kokoro-nvidia"
    RUN_FLAGS="--gpus all"
elif grep -q "Strix" /proc/cpuinfo || (lspci 2>/dev/null | grep -q "Strix"); then
    echo "AMD Strix detected."
    TARGET="strix"
    DOCKERFILE="Dockerfile.strix"
    IMAGE_NAME="epub2tts-kokoro-strix"
    RUN_FLAGS="--device /dev/kfd --device /dev/dri"
elif [ -e /dev/kfd ]; then
    echo "AMD GPU detected."
    TARGET="amd"
    DOCKERFILE="Dockerfile.amd"
    IMAGE_NAME="epub2tts-kokoro-amd"
    RUN_FLAGS="--device /dev/kfd --device /dev/dri"
elif [ "$(uname -m)" = "arm64" ]; then
    echo "ARM64 (likely macOS/Apple Silicon) detected."
    TARGET="macos"
    DOCKERFILE="Dockerfile.macos"
    IMAGE_NAME="epub2tts-kokoro-macos"
    RUN_FLAGS=""
else
    echo "No specific accelerator detected. Defaulting to CPU (Intel/Generic)."
    TARGET="cpu"
    DOCKERFILE="Dockerfile.intel"
    IMAGE_NAME="epub2tts-kokoro-cpu"
    RUN_FLAGS=""
fi

echo "Building image $IMAGE_NAME using $DOCKERFILE..."
$RUNTIME build -f $DOCKERFILE -t $IMAGE_NAME .

echo "Running $IMAGE_NAME..."
# Ensure cache directory exists
mkdir -p "$HOME/.cache/kokoro_hf_cache"

$RUNTIME run --rm -it $RUN_FLAGS \
    -v "$(pwd):/data" \
    -v "$HOME/.cache/kokoro_hf_cache:/root/.cache/huggingface" \
    $IMAGE_NAME "$@"
