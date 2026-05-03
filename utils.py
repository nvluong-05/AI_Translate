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

def get_selected_text():
    keyboard.press_and_release('ctrl+c')
    time.sleep(0.3)
    return pyperclip.paste().strip()

def get_mouse_position():
    return mouse.position()

# # --- (TESTING) ---
# if __name__ == "__main__":
#     init_db()
    
#     print("Đang thử lưu từ 'Innovation'...")
#     success = add_to_notebook("Innovation", "Sự đổi mới", "/ˌɪn.əˈveɪ.ʃən/", "Tech")
#     if success:
#         print("Lưu thành công!")
    
#     print("\n--- BÀI TEST COPY ---")
#     print("Bây giờ bạn hãy bôi đen một đoạn chữ bất kỳ trên màn hình...")
#     print("App sẽ đợi 3 giây để bạn bôi đen...")
#     time.sleep(3)
    
#     text = get_selected_text()
#     print(f"Văn bản bạn vừa bôi đen là: '{text}'")
    
#     pos = get_mouse_position()
#     print(f"Tọa độ chuột hiện tại: {pos}")
