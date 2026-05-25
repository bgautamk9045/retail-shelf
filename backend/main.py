# backend/main.py — full rewrite with safe imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import cv2

load_dotenv()

app = FastAPI(title="Shelf Monitor API")
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── lazy globals (loaded once on first /scan call, not at startup) ──
_detector = None
_camera   = None

def get_detector():
    global _detector
    if _detector is None:
        from model.detector import ShelfDetector
        _detector = ShelfDetector()   # loads YOLOv8 here
    return _detector

def get_camera():
    global _camera
    if _camera is None:
        from model.camera import CameraReader
        _camera = CameraReader()
    return _camera

# ── shelf config ──────────────────────────────────────────────────
SHELF_ZONES = {
    "A1": (0,   0,   213, 320),
    "A2": (213, 0,   426, 320),
    "A3": (426, 0,   640, 320),
    "B1": (0,   320, 213, 640),
    "B2": (213, 320, 426, 640),
    "B3": (426, 320, 640, 640),
}

PLANOGRAM = {
    "A1": "coca_cola_330ml",
    "A2": "pepsi_330ml",
    "A3": "sprite_330ml",
    "B1": "lays_classic",
    "B2": "lays_sour_cream",
    "B3": "doritos_nacho",
}

active_ws = []

async def broadcast(message: dict):
    for ws in active_ws[:]:
        try:
            await ws.send_json(message)
        except:
            active_ws.remove(ws)

# ── endpoints ─────────────────────────────────────────────────────

#Basic health check. Returns API status. Use this to verify the Docker container started correctly.
@app.get("/")
async def root():
    return {"status": "Shelf Monitor API is running"}


#Deep health check. Confirms both FastAPI and MongoDB connection are live.
@app.get("/health")
async def health():
    return {"mongo": "connected", "api": "ok"}


#WebSocket endpoint. Dashboard connects here on page load. Server pushes JSON alert message the moment a scan finds out-of-stock or misplaced items.
@app.websocket("/ws/alerts")
async def websocket_alerts(ws: WebSocket):
    await ws.accept()
    active_ws.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in active_ws:
            active_ws.remove(ws)


#THE MAIN ACTION. Triggers one full cycle: capture → detect → compare planogram → save to MongoDB → upload to S3 → broadcast WebSocket alert.
@app.post("/scan")
async def scan_shelf():
    try:
        detector = get_detector()
        camera   = get_camera()

        frame = camera.read_frame()
        if frame is None:
            return {"error": "No frame from camera"}

        analysis = detector.analyze_shelf(frame, SHELF_ZONES, PLANOGRAM)

        # Save frame locally (S3 upload optional)
        frame_filename = f"data/frames/{int(analysis.timestamp)}.jpg"
        cv2.imwrite(frame_filename, frame)

        # Try S3 upload (won't crash if it fails)
        frame_key = frame_filename
        try:
            from backend.s3_uploader import upload_frame
            _, buf = cv2.imencode(".jpg", frame)
            frame_key = await upload_frame(buf.tobytes(), analysis.timestamp)
        except Exception as e:
            print(f"S3 upload skipped: {e}")

        # Save to MongoDB (won't crash if it fails)
        try:
            from backend.database import db
            doc = {
                "timestamp":       analysis.timestamp,
                "out_of_stock":    analysis.out_of_stock,
                "misplaced":       analysis.misplaced,
                "detection_count": len(analysis.detections),
                "frame_path":      frame_key,
            }
            await db.events.insert_one(doc)
        except Exception as e:
            print(f"MongoDB save skipped: {e}")

        # Broadcast alert if issues found
        if analysis.out_of_stock or analysis.misplaced:
            await broadcast({
                "type":         "alert",
                "out_of_stock": analysis.out_of_stock,
                "misplaced":    analysis.misplaced,
                "timestamp":    analysis.timestamp,
            })

        return {
            "ok":          True,
            "timestamp":   analysis.timestamp,
            "detections":  len(analysis.detections),
            "out_of_stock": analysis.out_of_stock,
            "misplaced":   analysis.misplaced,
            "issues":      len(analysis.out_of_stock) + len(analysis.misplaced),
        }

    except Exception as e:
        return {"error": str(e)}


#Returns last 50 scan results from MongoDB sorted newest-first. Add ?limit=N to change count. Each record has full detection detail + S3 frame key.
@app.get("/events")   
async def get_events(limit: int = 50):
    try:
        from backend.database import db
        events = await db.events.find().sort("timestamp", -1).to_list(limit)
        for e in events:
            e["_id"] = str(e["_id"])
        return events
    except Exception as e:
        return {"error": str(e), "events": []}


#Returns the current expected shelf layout — which product goes in which zone. In production this is editable by store managers.
@app.get("/planogram")
async def get_planogram():
    return PLANOGRAM