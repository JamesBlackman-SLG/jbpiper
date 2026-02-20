import asyncio
import os
import subprocess
import tempfile
import wave

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from piper import PiperVoice
from piper.config import SynthesisConfig

DEVICE = "alsa_output.pci-0000_0d_00.4.analog-stereo"
BASE_DIR = os.path.dirname(__file__)
GAP_SECONDS = 1.0

VOICES = {
    "alba": os.path.join(BASE_DIR, "en_GB-alba-medium.onnx"),
    "alan": os.path.join(BASE_DIR, "en_GB-northern_english_male-medium.onnx"),
}
DEFAULT_VOICE = "alba"

loaded_voices: dict[str, PiperVoice] = {}
speech_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()


async def speech_worker():
    first = True
    while True:
        text, voice_name = await speech_queue.get()
        if not first:
            await asyncio.sleep(GAP_SECONDS)
        first = False
        voice = loaded_voices[voice_name]
        await asyncio.to_thread(_synthesize_and_play, text, voice)
        speech_queue.task_done()


def _synthesize_and_play(text: str, voice: PiperVoice):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        with wave.open(wav_path, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file, syn_config=SynthesisConfig(length_scale=1.2))
        subprocess.run(["paplay", f"--device={DEVICE}", wav_path])
    finally:
        os.unlink(wav_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for name, path in VOICES.items():
        if os.path.exists(path):
            loaded_voices[name] = PiperVoice.load(path)
    task = asyncio.create_task(speech_worker())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


class SpeakRequest(BaseModel):
    text: str
    voice: str = DEFAULT_VOICE


@app.post("/speak")
async def speak(req: SpeakRequest):
    if req.voice not in loaded_voices:
        raise HTTPException(status_code=400, detail=f"Unknown voice '{req.voice}'. Available: {list(loaded_voices.keys())}")
    await speech_queue.put((req.text, req.voice))
    return {"status": "queued", "text": req.text, "voice": req.voice, "queue_size": speech_queue.qsize()}


@app.get("/voices")
async def list_voices():
    return {"voices": list(loaded_voices.keys()), "default": DEFAULT_VOICE}
