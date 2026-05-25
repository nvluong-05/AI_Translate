import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

KEYS = [
    os.getenv("GEMINI_API_KEY_1") or "PLACEHOLDER_KEY_1",
    os.getenv("GEMINI_API_KEY_2") or "PLACEHOLDER_KEY_2",
    os.getenv("GEMINI_API_KEY_3") or "PLACEHOLDER_KEY_3",
]

KEYS = [k for k in KEYS if not k.startswith("PLACEHOLDER")]


class Translator:
    def __init__(self):
        self._keys = KEYS.copy() if KEYS else ["PLACEHOLDER_KEY_1"]
        self._key_index = 0
        self._update_url()

    def _update_url(self):
        key = self._keys[self._key_index]
        self.api_url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-2.0-flash:generateContent?key={key}"
        )

    def _rotate_key(self):
        """Chuyển sang key tiếp theo"""
        self._key_index = (self._key_index + 1) % len(self._keys)
        self._update_url()
        print(f"Đổi sang key #{self._key_index + 1}")

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

        total_attempts = len(self._keys) * 2

        for attempt in range(total_attempts):
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
                    error_msg = data["error"].get("message", "")
                    if "quota" in error_msg.lower() or "429" in str(data["error"].get("code", "")):
                        if len(self._keys) > 1:
                            self._rotate_key()
                            time.sleep(1)
                            continue
                    return f"Lỗi dịch thuật: {error_msg}"

                return data["candidates"][0]["content"]["parts"][0]["text"].strip()

            except Exception as e:
                if attempt < total_attempts - 1:
                    time.sleep(3)
                    continue
                return f"Lỗi kết nối: {str(e)}"

        return "Tất cả key đã hết quota. Vui lòng thử lại sau."


if __name__ == "__main__":
    bot = Translator()
    print(bot.translate_text("Persistence"))
    print(bot.translate_text("This is a long sentence about technology."))