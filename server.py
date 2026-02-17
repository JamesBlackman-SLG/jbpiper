import asyncio
import os
import subprocess
import tempfile
import wave

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from piper import PiperVoice
from piper.config import SynthesisConfig

DEVICE = "alsa_output.pci-0000_0d_00.4.analog-stereo"
MODEL = os.path.join(os.path.dirname(__file__), "en_GB-alba-medium.onnx")
GAP_SECONDS = 1.0

voice = PiperVoice.load(MODEL)
speech_queue: asyncio.Queue[str] = asyncio.Queue()


async def speech_worker():
    first = True
    while True:
        text = await speech_queue.get()
        if not first:
            await asyncio.sleep(GAP_SECONDS)
        first = False
        await asyncio.to_thread(_synthesize_and_play, text)
        speech_queue.task_done()


def _synthesize_and_play(text: str):
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
    task = asyncio.create_task(speech_worker())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


class SpeakRequest(BaseModel):
    text: str


@app.post("/speak")
async def speak(req: SpeakRequest):
    await speech_queue.put(req.text)
    return {"status": "queued", "text": req.text, "queue_size": speech_queue.qsize()}
