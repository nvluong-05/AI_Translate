import sqlite3
import pyautogui as mouse
import keyboard
import time
import pyperclip

def init_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    cursor.execute(''' CREATE TABLE IF NOT EXISTS data 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    word TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    phonetics TEXT NOT NULL,
                    tag TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    print("Database sẵn sàng!")

def add_to_notebook(word, definition, phonetics="", tag="General"):
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO data (word, definition, phonetics, tag) 
                          VALUES (?, ?, ?, ?)''', (word, definition, phonetics, tag))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Lỗi lưu trữ: {e}")
        return False
