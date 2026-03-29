import os
import cv2
import numpy as np
import requests
import time
import threading
import io
import logging
from tflite_runtime.interpreter import Interpreter

# LOGGING SETUP
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# CONFIGURATION
BOT_TOKEN =os.getenv("BOT_TOKEN")
CHAT_ID =os.getenv("CHAT_ID")     
COOLDOWN    = 15                          # seconds between alerts
THRESHOLD   = 0.5                         # minimum detection confidence
MODEL_PATH  = "../model/detect.tflite"
LABEL_PATH  = "../model/labelmap.txt"
TARGET_LABEL = "person"


# MODEL SETUP
def load_model(model_path: str):
    interp = Interpreter(model_path=model_path)
    interp.allocate_tensors()
    return interp, interp.get_input_details(), interp.get_output_details()

def load_labels(label_path: str) -> list[str]:
    with open(label_path, "r") as f:
        return [line.strip() for line in f.readlines()]

try:
    interpreter, input_details, output_details = load_model(MODEL_PATH)
    labels = load_labels(LABEL_PATH)
    log.info("Model and labels loaded successfully.")
except FileNotFoundError as e:
    log.error(f"Startup failed: {e}")
    raise SystemExit(1)


# TELEGRAM ALERT
def send_alert(frame: np.ndarray, score: float) -> None:
    """Encode frame as JPEG and send to Telegram. Runs in a daemon thread."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            log.error("Failed to encode frame as JPEG.")
            return

        files = {"photo": ("alert.jpg", io.BytesIO(buffer), "image/jpeg")}
        data  = {
            "chat_id": CHAT_ID,
            "caption": f"🚨 Person detected! Confidence: {score:.0%}"
        }

        resp = requests.post(url, data=data, files=files, timeout=10)
        resp.raise_for_status()
        log.info("Alert sent to Telegram successfully.")

    except requests.exceptions.HTTPError as e:
        log.error(f"Telegram HTTP error: {e} | Response: {e.response.text}")
    except requests.exceptions.RequestException as e:
        log.error(f"Telegram request failed: {e}")
    except Exception as e:
        log.error(f"Unexpected error in send_alert: {e}")


# INFERENCE
def run_inference(frame: np.ndarray):
    """
    Resize, preprocess and run TFLite inference on a frame.
    Returns (best_score, best_box) or (0, None) if no target found.
    """
    h_in = input_details[0]['shape'][1]
    w_in = input_details[0]['shape'][2]

    img = cv2.resize(frame, (w_in, h_in))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    input_data = np.expand_dims(img, axis=0).astype(np.uint8)

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    boxes   = interpreter.get_tensor(output_details[0]['index'])[0]
    classes = interpreter.get_tensor(output_details[1]['index'])[0]
    scores  = interpreter.get_tensor(output_details[2]['index'])[0]

    best_score = 0.0
    best_box   = None

    for i, score in enumerate(scores):
        if score < THRESHOLD:
            continue
        class_id = int(classes[i])
        label_idx = class_id + 1                        # labelmap has a blank first line
        if label_idx >= len(labels):
            continue
        if labels[label_idx] == TARGET_LABEL and score > best_score:
            best_score = score
            best_box   = boxes[i]

    return best_score, best_box


# DRAW DETECTION
def draw_detection(frame: np.ndarray, box, score: float) -> None:
    h, w = frame.shape[:2]
    ymin, xmin, ymax, xmax = box
    x1, x2 = int(xmin * w), int(xmax * w)
    y1, y2 = int(ymin * h), int(ymax * h)

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(
        frame,
        f"{TARGET_LABEL.upper()} {score:.0%}",
        (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2
    )


# MAIN LOOP
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        log.error("Could not open camera.")
        raise SystemExit(1)

    log.info("Surveillance running — press ESC to quit.")
    last_alert_time = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                log.warning("Failed to grab frame. Retrying...")
                time.sleep(0.1)
                continue

            score, box = run_inference(frame)

            if box is not None:
                draw_detection(frame, box, score)

                now = time.time()
                if now - last_alert_time >= COOLDOWN:
                    log.info(f"Person detected ({score:.0%}) — sending alert…")
                    threading.Thread(
                        target=send_alert,
                        args=(frame.copy(), score),
                        daemon=True
                    ).start()
                    last_alert_time = now

            cv2.imshow("Edge AI Surveillance", frame)

            if cv2.waitKey(1) == 27:   # ESC
                log.info("ESC pressed — shutting down.")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        log.info("Camera released. Goodbye.")

if __name__ == "__main__":
    main()

