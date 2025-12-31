import os
import sys
import torch
import soundfile
import numpy as np
from kokoro import KPipeline

if len(sys.argv) != 3:
    print("Usage: python read.py <text_file> <speaker_name>")
    print("Example: python read.py greeting.txt am_heart")
    sys.exit(1)

text_file = sys.argv[1]
speaker = sys.argv[2]

# Check if text file exists
if not os.path.exists(text_file):
    print(f"Error: Text file '{text_file}' not found.")
    sys.exit(1)

# Read the text from the file
with open(text_file, 'r', encoding='utf-8') as f:
    text = f.read()

# Generate output filename (replace .txt extension with .wav)
output_file = os.path.splitext(text_file)[0] + '.wav'

# Check for CUDA GPU
if torch.cuda.is_available():
    print('CUDA GPU available')
    torch.set_default_device('cuda')

print(f"Generating audio for speaker '{speaker}' from '{text_file}'...")

# Create pipeline with language code (first character of speaker name)
pipeline = KPipeline(lang_code=speaker[0])

# Generate audio segments
audio_segments = []
for gs, ps, audio in pipeline(text, voice=speaker, speed=1, split_pattern=r'\n\n\n'):
    audio_segments.append(audio)

# Concatenate all audio segments
final_audio = np.concatenate(audio_segments)

# Write to wav file
soundfile.write(output_file, final_audio, 24000)

print(f"Audio saved to '{output_file}'")
