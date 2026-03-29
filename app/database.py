import sqlite3
import os

DB_PATH = "data/surveillance.db"

def init_db():
    """Creates the data folders and SQLite table if they don't exist."""
    # Ensure the directories exist
    os.makedirs("data/captures", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            confidence REAL,
            image_path TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("💾 Database initialized.")

def log_detection(confidence, image_path):
    """Logs a new threat detection to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO detections (confidence, image_path) 
        VALUES (?, ?)
    ''', (confidence, image_path))
    conn.commit()
    conn.close()