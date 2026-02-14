FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends pulseaudio-utils && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir piper-tts==1.4.1 fastapi==0.129.0 uvicorn==0.40.0

WORKDIR /app
COPY server.py .
COPY en_GB-alba-medium.onnx en_GB-alba-medium.onnx.json ./

EXPOSE 39271

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "39271"]
