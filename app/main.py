import cv2
import numpy as np
import requests
import time
import threading
import io
import os
from dotenv import load_dotenv
from tflite_runtime.interpreter import Interpreter
import database
import api

# CONFIGURATION & SECRETS
load_dotenv() 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
COOLDOWN = 15  # seconds
last_alert_time = 0

if not BOT_TOKEN or not CHAT_ID:
    print("Error: Missing Telegram credentials in .env file.")
    exit()

# PASTE YOUR COORDINATES HERE (From get_coords.py)
RESTRICTED_ZONE = np.array([(88, 10), (99, 468), (634, 473), (628, 10)], np.int32)


# MODEL SETUP
interpreter = Interpreter(model_path="models/detect.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

try:
    with open("models/labelmap.txt", "r") as f:
        labels = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    print("Error: models/labelmap.txt not found.")
    exit()


# THREADED TELEGRAM ALERT
def send_alert(frame_to_send):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        success, buffer = cv2.imencode('.jpg', frame_to_send)
        if not success:
            print("Failed to encode image.")
            return
            
        io_buf = io.BytesIO(buffer)
        files = {"photo": ("alert.jpg", io_buf, "image/jpeg")}
        data = {"chat_id": CHAT_ID, "caption": "🚨 Trespasser in restricted zone!"}
        
        response = requests.post(url, data=data, files=files)
        response.raise_for_status() 
        print("Alert sent successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"Telegram alert failed: {e}")

# MAIN LOOP
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera error.")
    exit()
database.init_db()

# Start the Web Dashboard in a background thread
threading.Thread(target=api.run_server, daemon=True).start()
print("🌐 Web Dashboard live at: http://192.168.1.112:8000")
print("System running... Press ESC to exit.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # TFLite Preprocessing
        img = cv2.resize(frame, (300, 300))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        input_data = np.expand_dims(img, axis=0).astype(np.uint8)

        # Inference
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()

        boxes = interpreter.get_tensor(output_details[0]['index'])[0]
        classes = interpreter.get_tensor(output_details[1]['index'])[0]
        scores = interpreter.get_tensor(output_details[2]['index'])[0]

        best_score = 0
        best_box = None

        for i in range(len(scores)):
            if scores[i] > 0.5:
                class_id = int(classes[i])
                if class_id + 1 < len(labels) and labels[class_id + 1] == "person":
                    if scores[i] > best_score:
                        best_score = scores[i]
                        best_box = boxes[i]

        # Draw the Restricted Zone permanently on the frame
        cv2.polylines(frame, [RESTRICTED_ZONE], isClosed=True, color=(255, 0, 0), thickness=2)
        cv2.putText(frame, "RESTRICTED", (RESTRICTED_ZONE[0][0], RESTRICTED_ZONE[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Action Logic
        # Action Logic
        if best_box is not None:
            h, w, _ = frame.shape
            ymin, xmin, ymax, xmax = best_box
            xmin, xmax, ymin, ymax = int(xmin * w), int(xmax * w), int(ymin * h), int(ymax * h)

            # 1. Locate the person's Feet AND Center Mass
            center_x = int((xmin + xmax) / 2)
            feet_y = ymax
            center_y = int((ymin + ymax) / 2)

            # Draw dots so you can visually debug both points on the web dashboard
            cv2.circle(frame, (center_x, feet_y), radius=5, color=(0, 255, 255), thickness=-1) # Feet Dot
            cv2.circle(frame, (center_x, center_y), radius=5, color=(255, 0, 255), thickness=-1) # Center Dot

            # 2. Spatial Logic: Are the feet OR the center inside the zone?
            inside_feet = cv2.pointPolygonTest(RESTRICTED_ZONE, (center_x, feet_y), False)
            inside_center = cv2.pointPolygonTest(RESTRICTED_ZONE, (center_x, center_y), False)

            # If either point >= 0, they have breached the zone
            if inside_feet >= 0 or inside_center >= 0:
                # Inside: Red Box + Alert
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 0, 255), 3)
                cv2.putText(frame, f"INTRUDER {best_score:.2f}", (xmin, ymin-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                current_time = time.time()
                if current_time - last_alert_time > COOLDOWN:
                    print("Intruder inside zone! Logging and sending alert...")
                    
                    # Log to DB
                    filename = f"data/captures/threat_{int(current_time)}.jpg"
                    cv2.imwrite(filename, frame)
                    database.log_detection(float(best_score), filename)
                    
                    # Send Telegram Alert
                    threading.Thread(target=send_alert, args=(frame.copy(),), daemon=True).start()
                    
                    last_alert_time = current_time
            else:
                # Outside: Green Box, No Alert
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                cv2.putText(frame, f"SAFE {best_score:.2f}", (xmin, ymin-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Send a copy of the frame to the web server stream
        api.update_frame(frame)

        cv2.imshow("Edge AI Surveillance", frame)
        if cv2.waitKey(1) == 27: 
            break

finally:
    cap.release()
    cv2.destroyAllWindows()