import asyncio
import math
import os
import struct
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
        if text == "__beep__":
            freq, dur = voice_name.split(",")
            await asyncio.to_thread(_generate_and_play_beep, float(freq), float(dur))
        else:
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


def _generate_and_play_beep(frequency: float, duration: float):
    sample_rate = 22050
    num_samples = int(sample_rate * duration)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        with wave.open(wav_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            samples = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                value = int(32767 * 0.8 * math.sin(2 * math.pi * frequency * t))
                samples += struct.pack("<h", value)
            wav_file.writeframes(bytes(samples))
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


class BeepRequest(BaseModel):
    frequency: float = 440.0
    duration: float = 0.3


@app.post("/beep")
async def beep(req: BeepRequest):
    await speech_queue.put(("__beep__", f"{req.frequency},{req.duration}"))
    return {"status": "queued", "frequency": req.frequency, "duration": req.duration, "queue_size": speech_queue.qsize()}


@app.get("/voices")
async def list_voices():
    return {"voices": list(loaded_voices.keys()), "default": DEFAULT_VOICE}
