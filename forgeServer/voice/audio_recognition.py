import keyboard
import openai
import sounddevice as sd
import tempfile
import numpy as np
from minecraft_interface import attention_grab
from scipy.io.wavfile import write

# Whisper 음성 인식 함수
def record_and_transcribe(fs=44100,chunk_duration=0.5):
    audio_chunks = []
    try:
        with sd.InputStream(samplerate=fs, channels=1, dtype='int16') as stream:
            while keyboard.is_pressed('c'):
                #Grab the Mobs Attention
                attention_grab()
                chunk, _ = stream.read(int(fs * chunk_duration))
                audio_chunks.append(chunk)
                print(f"⏺️ ...recording {len(audio_chunks)*chunk_duration:.1f}s", end="\r")

        # Combine all chunks into one array
        final_audio = np.concatenate(audio_chunks, axis=0)

        # Save to temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            write(tmpfile.name, fs, final_audio)
            with open(tmpfile.name, "rb") as f:
                result = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
                    
                return result.text

    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user.")
        return None