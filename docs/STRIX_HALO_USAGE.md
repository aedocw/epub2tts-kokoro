# Running on AMD Strix Halo (Ryzen AI 300 / Max 300 Series)

AMD Strix Halo APUs feature RDNA 3.5 graphics (gfx1151) and an XDNA 2 NPU. Currently, the best way to run `epub2tts-kokoro` with hardware acceleration on these platforms is using the integrated RDNA 3.5 GPU via ROCm.

## Prerequisites

- **Linux OS**: A modern Linux distribution (Ubuntu 22.04/24.04, Fedora 40+, etc.)
- **ROCm Drivers**: Ensure you have the AMDGPU drivers installed.
- **Docker**: Installed and configured with ROCm support (usually requires `--device /dev/kfd --device /dev/dri`).

## Building the Image

We use a Dockerfile based on `rocm/pytorch:latest`, which currently provides a nightly build of PyTorch (e.g., 2.9.x) compatible with ROCm 7.x and RDNA 3.5.

```bash
docker build -f Dockerfile.strix -t epub2tts-strix .
```

## Running the Container

Run the container mapping your current directory (containing the epub) to `/data` inside the container. We also need to pass the necessary devices for ROCm access.

```bash
docker run --rm -it \
    --device /dev/kfd \
    --device /dev/dri \
    --group-add video \
    -v $(pwd):/data \
    epub2tts-strix <your_book.epub>
```

## Caching Model Weights

To avoid re-downloading the model weights (approx. 350MB) every time, you can mount a volume for the Hugging Face cache.

```bash
docker run --rm -it \
    --device /dev/kfd \
    --device /dev/dri \
    --group-add video \
    -v $(pwd):/data \
    -v $HOME/.cache/huggingface:/root/.cache/huggingface \
    epub2tts-strix <your_book.epub>
```

## Troubleshooting

### MIOpen / Inline Assembly Errors
If you encounter errors like `miopenStatusUnknownError` or `cannot compile inline asm`, it indicates a compatibility issue with the MIOpen kernels and the RDNA 3.5 architecture. Try the following environment variables:

1.  **Enable Experimental Attention Kernels**:
    ```bash
    docker run -e TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1 ...
    ```
    This switches to Triton-based kernels for attention, which may bypass the failing MIOpen kernels.

2.  **Override GFX Version**:
    The Dockerfile sets `HSA_OVERRIDE_GFX_VERSION=11.5.1`. If this fails, try spoofing RDNA 3 (gfx1100):
    ```bash
    docker run -e HSA_OVERRIDE_GFX_VERSION=11.0.0 ...
    ```

3.  **Disable MIOpen for Specific Ops (Advanced)**:
    If the above fails, you can try disabling MIOpen compilation cache (already disabled in Dockerfile) or forcing a different find mode:
    ```bash
    docker run -e MIOPEN_FIND_MODE=1 ...
    ```

Direct NPU support via PyTorch is currently experimental and often requires converting models to ONNX and using the Ryzen AI software stack. For now, the RDNA 3.5 GPU path (ROCm) is recommended for the best balance of performance and compatibility with this project.
