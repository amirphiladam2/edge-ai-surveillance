import cv2
import numpy as np
from tflite_runtime.interpreter import Interpreter

# Load model
interpreter = Interpreter(model_path="../model/detect.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Load labels
with open("../model/labelmap.txt", "r") as f:
    labels = [line.strip() for line in f.readlines()]

# Start camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera error")
    exit()

print("System running... Press ESC to exit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Preprocess
    img = cv2.resize(frame, (300, 300))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    input_data = np.expand_dims(img, axis=0).astype(np.uint8)

    # Inference
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    boxes = interpreter.get_tensor(output_details[0]['index'])[0]
    classes = interpreter.get_tensor(output_details[1]['index'])[0]
    scores = interpreter.get_tensor(output_details[2]['index'])[0]

    for i in range(len(scores)):
        if scores[i] > 0.5:
            class_id = int(classes[i])

            # Fix label index shift
            if class_id + 1 < len(labels):
                label = labels[class_id + 1]
            else:
                label = "unknown"

            if label == "person":
                h, w, _ = frame.shape
                ymin, xmin, ymax, xmax = boxes[i]

                xmin = int(xmin * w)
                xmax = int(xmax * w)
                ymin = int(ymin * h)
                ymax = int(ymax * h)

                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0,255,0), 2)
                cv2.putText(frame, "PERSON", (xmin, ymin-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    cv2.imshow("Edge AI Detection", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()