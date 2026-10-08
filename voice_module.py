import sounddevice as sd
import numpy as np
import wave
import whisper
import warnings
import os
import time
import requests
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "google/gemini-2.0-flash-lite",
    "meta-llama/llama-3.3-70b-instruct",
    "openrouter/auto",
]

def record_audio(duration=5, fs=44100, filename="temp_audio.wav"):
    """Hàm thu âm từ microphone"""
    print(f"🎙️ Bắt đầu thu âm trong {duration} giây...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait() 
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(recording.tobytes())
    print(f"✅ Đã lưu file: {filename}")
    return filename

def transcribe_audio(audio_file):
    """Hàm bóc băng âm thanh bằng Whisper"""
    print("⏳ AI Whisper đang phân tích âm thanh...")
    try:
        model = whisper.load_model("base")
        result = model.transcribe(audio_file)
        text = result["text"].strip()
        print(f"🗣️ Tiếng Anh: {text}")
        return text
    except Exception as e:
        print(f"❌ Lỗi Whisper: {e}")
        return None

def translate_to_vietnamese(english_text, api_key=None):
    """Hàm dịch sang tiếng Việt qua OpenRouter dùng requests"""

    key_to_use = api_key if api_key and api_key != "YOUR_KEY" else os.getenv("OPENROUTER_API_KEY")
    
    if not key_to_use:
        return "❌ Lỗi: Chưa cấu hình API Key trong file .env"

    prompt = f"""Bạn là một giáo viên tiếng Anh. Hãy xử lý câu sau: "{english_text}"
    Yêu cầu:
    1. Dịch câu đó sang tiếng Việt một cách tự nhiên nhất.
    2. Kiểm tra xem câu tiếng Anh gốc có lỗi ngữ pháp, dùng từ sai, hoặc nghe có vẻ không tự nhiên hay không. Nếu có, hãy sửa lại cho chuẩn. Nếu câu đã hoàn hảo, bỏ qua phần sửa lỗi.
    
    Chỉ trả về theo đúng định dạng sau, tuyệt đối không giải thích thêm:
    Dịch: [Bản dịch tiếng Việt]
    Sửa lỗi (nếu có): [Câu tiếng Anh đã được sửa cho chuẩn]"""

    for model in MODELS:
        for attempt in range(2):
            try:
                response = requests.post(
                    API_URL,
                    headers={
                        "Authorization": f"Bearer {key_to_use}",
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
            except Exception as e:
                print(f"Lỗi gọi API {model}: {e}")
                break

    return "❌ Hệ thống dịch bận, vui lòng thử lại."

if __name__ == "__main__":
    audio_file = record_audio(duration=5)
    english_text = transcribe_audio(audio_file)
    
    if english_text:
        translated_text = translate_to_vietnamese(english_text)
        print(f"🇻🇳 Tiếng Việt: {translated_text}")