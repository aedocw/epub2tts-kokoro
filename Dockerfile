# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies if requirements.txt exists
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Make sure the binary is executable
RUN chmod +x epub2tts-kokoro

# Set the entrypoint to the binary
ENTRYPOINT ["./epub2tts-kokoro"]