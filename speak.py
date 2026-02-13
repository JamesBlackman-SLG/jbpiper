import subprocess
import tempfile
import wave
from piper import PiperVoice

DEVICE = "alsa_output.pci-0000_0d_00.4.analog-stereo"
MODEL = "en_US-lessac-medium.onnx"
TEXT = "Hello, how are you doing?"

voice = PiperVoice.load(MODEL)

with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    wav_path = f.name

with wave.open(wav_path, "wb") as wav_file:
    voice.synthesize_wav(TEXT, wav_file)

subprocess.run(["paplay", f"--device={DEVICE}", wav_path])
