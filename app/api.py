from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import cv2
import threading
import time

app = FastAPI()

# Setup templates and static files (for serving the saved images)
templates = Jinja2Templates(directory="templates")
app.mount("/data", StaticFiles(directory="data"), name="data")

# Global variables for the live video stream
current_frame = None
frame_lock = threading.Lock()

def update_frame(frame):
    """Called by main.py to safely update the web stream frame."""
    global current_frame
    with frame_lock:
        current_frame = frame.copy()

def generate_mjpeg():
    """Continuously yields the latest frame for the browser."""
    global current_frame
    while True:
        with frame_lock:
            if current_frame is None:
                continue
            success, buffer = cv2.imencode('.jpg', current_frame)
            if not success:
                continue
            frame_bytes = buffer.tobytes()

        # Yield the frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05) # ~20 FPS limit to save CPU

@app.get("/video_feed")
def video_feed():
    """Endpoint for the live camera stream."""
    return StreamingResponse(generate_mjpeg(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/")
def read_root(request: Request):
    """The main dashboard UI. Fetches the last 10 logs from the database."""
    conn = sqlite3.connect("data/surveillance.db")
    cursor = conn.cursor()
    # Fetch the 10 most recent detections
    try:
        cursor.execute("SELECT timestamp, confidence, image_path FROM detections ORDER BY id DESC LIMIT 10")
        logs = cursor.fetchall()
    except sqlite3.OperationalError:
        logs = [] # Failsafe if the table is empty or locked
    finally:
        conn.close()

    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"logs": logs}
    )

def run_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")