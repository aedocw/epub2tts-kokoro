# Vulkan Docker Usage Guide

This guide explains how to build and run the `epub2tts-kokoro` container with Vulkan support.

> [!WARNING]
> **Experimental Support**: Standard PyTorch wheels for Linux typically do **not** come with the Vulkan backend enabled. This Dockerfile sets up the necessary system drivers and SDK, but `torch.is_vulkan_available()` may still return `False` unless you use a custom build of PyTorch.

## Prerequisites

- Linux system with a Vulkan-capable GPU.
- Docker installed.
- Host Vulkan drivers working (verify with `vulkaninfo` on host).

## Building the Image

Build the Docker image using the `Dockerfile.vulkan` file:

```bash
docker build -f Dockerfile.vulkan -t epub2tts-kokoro:vulkan .
```

## Running the Container

To run the container with Vulkan access, you need to map the host's Vulkan loader and drivers. The arguments can vary depending on your GPU vendor (AMD/Intel/Nvidia).

### Generic Linux (AMD/Intel)

You typically need to pass the render devices and map the Vulkan loader files if they aren't fully compatible inside.

```bash
docker run --rm -it \
  --device=/dev/dri \
  --group-add video \
  -v $(pwd):/data \
  epub2tts-kokoro:vulkan \
  [arguments]
```

### Nvidia

For Nvidia, you usually use the NVIDIA Container Toolkit:

```bash
docker run --rm -it \
  --gpus all \
  -v $(pwd):/data \
  epub2tts-kokoro:vulkan \
  [arguments]
```

## Verification

To check if PyTorch detects Vulkan inside the container:

```bash
docker run --rm -it \
  --device=/dev/dri \
  --group-add video \
  --entrypoint python3 \
  epub2tts-kokoro:vulkan \
  -c "import torch; print(f'Vulkan available: {torch.is_vulkan_available()}')"
```

If it returns `False`, it means the installed PyTorch version was not built with Vulkan support enabled.
