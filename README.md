# 🧠 Edge AI Smart Surveillance System

A real-time **Edge AI-powered surveillance system** built on Raspberry Pi that performs on-device human detection and sends instant alerts via Telegram — without relying on cloud processing.

---

## 🚀 Overview

This project demonstrates how to build a **low-cost, efficient, and privacy-focused security system** using:

* 🖥️ Local AI inference (TensorFlow Lite)
* 🎥 Real-time video processing (OpenCV)
* 📲 Instant alerting (Telegram Bot API)

All computation is done **on-device**, reducing latency and eliminating dependency on cloud services.

---

## ✨ Features

* ✅ Real-time human detection using Edge AI
* 📦 Lightweight TensorFlow Lite model (MobileNet SSD)
* 🎯 Single-object filtering (removes duplicate bounding boxes)
* 📸 Automatic snapshot capture on detection
* 📲 Instant Telegram alerts with image
* ⚡ Fully offline detection (no cloud required)
* 🧠 Optimized for Raspberry Pi (ARM architecture)

---

## 🏗️ System Architecture

> *(Insert your system architecture diagram below)*

![System Architecture](docs/architecture.png)

**Pipeline:**

Camera → Frame Capture → Preprocessing → TFLite Inference → Detection Filtering → Alert Trigger → Telegram Notification

---

## 🛠️ Tech Stack

| Component       | Technology                      |
| --------------- | ------------------------------- |
| Edge Device     | Raspberry Pi 5                  |
| Programming     | Python 3.11                     |
| Computer Vision | OpenCV                          |
| AI Model        | TensorFlow Lite (MobileNet SSD) |
| Communication   | Telegram Bot API                |
| Version Control | Git + GitHub                    |

---

## 📁 Project Structure

```
edge-ai-surveillance/
│
├── model/
│   ├── detect.tflite
│   └── labelmap.txt
│
├── src/
│   └── detect.py
│
├── docs/
│   ├── architecture.png
│   └── screenshots/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```
git clone https://github.com/your-username/edge-ai-surveillance.git
cd edge-ai-surveillance
```

---

### 2️⃣ Setup Python environment

```
python3.11 -m venv venv
source venv/bin/activate
```

---

### 3️⃣ Install dependencies

```
pip install "numpy<2" opencv-python requests pillow tflite-runtime==2.14.0
```

---

### 4️⃣ Download model

```
cd model
wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip
unzip coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip
```

---

### 5️⃣ Configure Telegram Bot

Update the following in `src/detect.py`:

```
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
```

---

### 6️⃣ Run the system

```
cd src
python detect.py
```

---

## 📸 Screenshots

> *(Add screenshots of detection and Telegram alerts here)*

### Detection Output

![Detection](docs/screenshots/detection.png)

### Telegram Alert

![Telegram Alert](docs/screenshots/telegram.png)

---

## 🧪 How It Works

1. Webcam captures live frames
2. Frames are resized and preprocessed
3. TensorFlow Lite model performs inference
4. Best “person” detection is selected
5. Bounding box is drawn
6. Snapshot is captured
7. Alert is sent via Telegram

---

## ⚠️ Limitations

* Detection accuracy depends on lighting conditions
* Optimized for single-person detection
* No object tracking (yet)
* CPU-bound inference (no hardware acceleration)

---

## 🚀 Future Improvements

* 🔁 Multi-object tracking
* 🌙 Night vision optimization
* 📊 Web dashboard for monitoring
* 🔊 IoT integration (ESP32 alarm trigger)
* ☁️ Optional cloud logging
* 🎥 Multi-camera support

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork the repo and submit pull requests.

---

## 📜 License

This project is open-source and available under the MIT License.

---

## 👨‍💻 Author

**Amir**
Embedded Systems & IoT Enthusiast

---

## If you found this useful

Give the repo a ⭐ on GitHub — it helps a lot!
