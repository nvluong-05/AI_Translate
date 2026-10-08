import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "google/gemini-2.0-flash-lite",
    "meta-llama/llama-3.3-70b-instruct",
    "openrouter/auto",
]

class Translator:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY") or "PLACEHOLDER_KEY"

    def translate_text(self, text):
        if not text:
            return None

        is_short = len(text.split()) <= 5

        if is_short:
            prompt = f"""Translate this word/phrase to Vietnamese: "{text}"
Reply in EXACTLY this format, each on its own line, nothing else:
Dịch: [1-3 short Vietnamese meanings, comma-separated, NO Chinese characters]
Phiên âm: [IPA pronunciation]
Ví dụ: [1 short example sentence in English ONLY, absolutely NO Vietnamese translation]"""
        else:
            prompt = f"""Dịch câu sau sang tiếng Việt: "{text}"
Chỉ trả về bản dịch ngắn gọn, sát nghĩa. Không giải thích thêm."""

        for model in MODELS:
            for attempt in range(2):
                try:
                    response = requests.post(
                        API_URL,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 150,
                        },
                        timeout=20,
                    )
                    data = response.json()

                    if "error" in data:
                        break

                    choices = data.get("choices", [])
                    if not choices:
                        break

                    content = choices[0].get("message", {}).get("content")
                    if not content:
                        break

                    return content.strip()

                except requests.Timeout:
                    if attempt < 1:
                        time.sleep(1)
                    continue
                except Exception:
                    break

        return "Không thể dịch lúc này. Vui lòng thử lại."


if __name__ == "__main__":
    bot = Translator()
    print(f"Key: {bot.api_key[:20]}...")
    print(bot.translate_text("audience"))
    print(bot.translate_text("organization"))
    print(bot.translate_text("This is a test sentence."))