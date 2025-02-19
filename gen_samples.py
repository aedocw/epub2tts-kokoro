import os
import torch
import soundfile
import numpy as np
from kokoro import KPipeline
from pydub import AudioSegment

speakers = ["af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica", "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky", "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", "am_puck", "am_santa", "bf_alice", "bf_emma", "bf_isabella", "bf_lily", "bm_daniel", "bm_fable", "bm_george", "bm_lewis",]

if torch.cuda.is_available():
    print('CUDA GPU available')
    torch.set_default_device('cuda')

for speaker in speakers:
    file = speaker + "_sample.wav"
    if os.path.exists(file):
        print(f"Sample for {speaker} already exists.")
        continue
    else:
        print(f"Creating {speaker}")
    pipeline = KPipeline(lang_code=speaker[0])
    sentence = f"Hello, this voice is {speaker[3:]}. The quick brown fox jumped over the lazy dog. The fish twisted and turned on the bent hook.  Press the pants and sew a button on the vest.  The swan dive was far short of perfect."
    audio_segments = []
    for gs, ps, audio in pipeline(sentence, voice=speaker, speed=1, split_pattern=r'\n\n\n'):
        audio_segments.append(audio)
    final_audio = np.concatenate(audio_segments)
    soundfile.write(file, final_audio, 24000)
