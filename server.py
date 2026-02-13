import os
import subprocess
import tempfile
import wave

from fastapi import FastAPI
from pydantic import BaseModel
from piper import PiperVoice

DEVICE = "alsa_output.pci-0000_0d_00.4.analog-stereo"
MODEL = os.path.join(os.path.dirname(__file__), "en_US-lessac-medium.onnx")

voice = PiperVoice.load(MODEL)
app = FastAPI()


class SpeakRequest(BaseModel):
    text: str


@app.post("/speak")
def speak(req: SpeakRequest):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        with wave.open(wav_path, "wb") as wav_file:
            voice.synthesize_wav(req.text, wav_file)
        subprocess.run(["paplay", f"--device={DEVICE}", wav_path])
    finally:
        os.unlink(wav_path)
    return {"status": "ok", "text": req.text}
