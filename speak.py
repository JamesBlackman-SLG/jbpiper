import subprocess
import tempfile
import wave
from piper import PiperVoice
from piper.config import SynthesisConfig

DEVICE = "alsa_output.pci-0000_0d_00.4.analog-stereo"
MODEL = "en_GB-alba-medium.onnx"
TEXT = "Good morning James, how are things going?"

voice = PiperVoice.load(MODEL)

with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    wav_path = f.name

with wave.open(wav_path, "wb") as wav_file:
    voice.synthesize_wav(TEXT, wav_file, syn_config=SynthesisConfig(length_scale=1.2))

subprocess.run(["paplay", f"--device={DEVICE}", wav_path])
