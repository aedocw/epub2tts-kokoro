# ROCm Docker Usage Guide

This guide explains how to build and run the `epub2tts-kokoro` container with ROCm support for AMD GPUs.

## Prerequisites

- Linux system with AMD GPU.
- [ROCm drivers](https://rocm.docs.amd.com/en/latest/deploy/linux/index.html) installed.
- Docker installed.

## Building the Image

Build the Docker image using the `Dockerfile.rocm` file:

```bash
docker build -f Dockerfile.rocm -t epub2tts-kokoro:rocm .
```

## Running the Container

To run the container with GPU access, you need to pass the KFD and DRI devices and the video group to the container.

```bash
docker run --rm -it \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  -v $(pwd):/data \
  epub2tts-kokoro:rocm \
  [arguments for epub2tts_kokoro.py]
```

### Example: Verify GPU Access

You can verify that PyTorch detects the AMD GPU inside the container by running:

```bash
docker run --rm -it \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --entrypoint python3 \
  epub2tts-kokoro:rocm \
  -c "import torch; print(f'CUDA (ROCm) available: {torch.cuda.is_available()}'); print(f'Device count: {torch.cuda.device_count()}')"
```

## Troubleshooting

- **Permission Denied**: Ensure your user is in the `docker` group and that you have permissions to access `/dev/kfd` and `/dev/dri`.
- **Image not found**: Make sure you built the image with the correct tag (`epub2tts-kokoro:rocm`) before trying to run it.
