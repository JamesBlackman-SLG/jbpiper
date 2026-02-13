# jbpiper

A local text-to-speech server powered by [Piper TTS](https://github.com/rhasspy/piper) and FastAPI. Sends synthesized audio to a PulseAudio device.

## Prerequisites

- Python 3.14+
- PulseAudio (for `paplay`)
- espeak-ng (required by Piper)

## Setup

1. Clone the repo and create a virtual environment:

```bash
git clone https://github.com/JamesBlackman-SLG/jbpiper.git
cd jbpiper
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install fastapi uvicorn piper-tts
```

3. Download a Piper voice model. The default config expects `en_US-lessac-medium`:

```bash
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

4. Update the `DEVICE` variable in `server.py` to match your PulseAudio sink. List available sinks with:

```bash
pactl list short sinks
```

## Usage

### Server

Start the FastAPI server:

```bash
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
```

Then send a POST request:

```bash
curl -X POST http://localhost:8000/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you doing?"}'
```

### Standalone script

For quick testing without the server:

```bash
source venv/bin/activate
python speak.py
```

Edit the `TEXT` variable in `speak.py` to change what is spoken.
