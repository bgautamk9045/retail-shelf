FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download YOLOv8 model at BUILD time (not runtime)
#RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

COPY . .

# Create data directories
RUN mkdir -p data/frames data/planograms

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]