import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

class Translator:
    def __init__(self):
        self.model = "openrouter/auto"
        self.api_key = os.getenv("OPENROUTER_API_KEY") or "PLACEHOLDER_KEY"

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
                    API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 150,
                    },
                    timeout=15,
                )
                data = response.json()

                if "error" in data:
                    return f"Lỗi dịch thuật: {data['error'].get('message', 'Unknown error')}"

                return data["choices"][0]["message"]["content"].strip()

            except Exception as e:
                if attempt < 2:
                    time.sleep(3)
                    continue
                return f"Lỗi kết nối: {str(e)}"


if __name__ == "__main__":
    bot = Translator()
    print(f"Key loaded: {bot.api_key[:20]}...")
    print(bot.translate_text("Persistence"))