import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or "PLACEHOLDER_KEY"

class Translator:
    def __init__(self):
        self.api_url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-2.0-flash:generateContent?key={API_KEY}"
        )

    def translate_text(self, text):
        if not text:
            return None

        is_short = len(text.split()) <= 5

        if is_short:
            prompt = f"""Dịch từ/cụm từ sau sang tiếng Việt: "{text}"
Trả về đúng định dạng này, không thêm gì khác:
Dịch: [1-3 nghĩa ngắn, cách nhau bằng dấu phẩy] | Phiên âm: [phiên âm IPA] | Ví dụ: [1 câu ngắn]"""
        else:
            prompt = f"""Dịch câu sau sang tiếng Việt: "{text}"
Chỉ trả về bản dịch ngắn gọn, sát nghĩa. Không giải thích thêm."""

        for attempt in range(3):
            try:
                response = requests.post(
                    self.api_url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"maxOutputTokens": 150}
                    },
                    timeout=15,
                )
                data = response.json()
                if "error" in data:
                    return f"Lỗi dịch thuật: {data['error'].get('message', 'Unknown error')}"
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                if attempt < 2:
                    time.sleep(5)
                    continue
                return f"Lỗi kết nối: {str(e)}"


if __name__ == "__main__":
    bot = Translator()
    print(bot.translate_text("Persistence"))
    print(bot.translate_text("This is a long sentence about technology."))