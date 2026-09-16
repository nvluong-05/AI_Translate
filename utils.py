import sqlite3
import os
import pyautogui as mouse
import pyperclip

APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AI_Translate")
os.makedirs(APP_DIR, exist_ok=True)
DB_PATH = os.path.join(APP_DIR, "data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS data 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    word TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    phonetics TEXT NOT NULL,
                    tag TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def add_to_notebook(word, definition, phonetics="", tag="General"):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO data (word, definition, phonetics, tag) 
                          VALUES (?, ?, ?, ?)''', (word, definition, phonetics, tag))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Lỗi lưu trữ: {e}")
        return False

def get_mouse_position():
    return mouse.position()