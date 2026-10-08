import sounddevice as sd
import numpy as np
import wave
import whisper
import warnings
from google import genai

warnings.filterwarnings("ignore")

GOOGLE_API_KEY = "AQ.Ab8RN6Ki7n2gR3a8huEtJmQ9wXMUiGdhN8cvIoQjUzcaqZeErQ"

def record_audio(filename="temp_audio.wav", duration=5, fs=44100):
    print("🎙️ Bắt đầu thu âm (hãy nói một câu tiếng Anh ngắn trong 5 giây)...")
    
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
    sd.wait()
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(recording.tobytes())
        
    print(f"✅ Đã lưu file: {filename}")
    return filename

def transcribe_audio(filename):
    print("⏳ AI Whisper đang phân tích âm thanh...")
    model = whisper.load_model("base")
    result = model.transcribe(filename, fp16=False)
    text = result["text"].strip()
    
    print("-" * 30)
    print(f"🗣️ Tiếng Anh: {text}")
    return text

def translate_to_vietnamese(text, api_key):
    print("⏳ Đang kết nối với hệ thống dịch vụ đám mây của Google...")
    
    try:
        client = genai.Client(api_key=api_key)
        
        models_to_try = [
            'gemini-3.8-flash', 
            'gemini-3.8-pro',   
            'gemini-1.5-flash', 
            'gemini-1.5-pro'
        ]
        
        prompt = f"""
        Người dùng vừa nói câu tiếng Anh (có thể bị sai ngữ pháp hoặc do nhận diện nhầm): "{text}"
        Hãy thực hiện 2 nhiệm vụ sau:
        1. Sửa lại thành câu tiếng Anh chuẩn xác nhất về mặt ngữ pháp và ngữ cảnh. Nếu câu gốc đã chuẩn, hãy giữ nguyên.
        2. Dịch câu đã sửa sang tiếng Việt thật tự nhiên.
        
        Trả về kết quả đúng theo định dạng 2 dòng dưới đây, tuyệt đối không giải thích gì thêm:
        ✨ Câu chuẩn: [Câu tiếng Anh đã sửa]
        🇻🇳 Dịch nghĩa: [Câu tiếng Việt]
        """
        
        for model_name in models_to_try:
            try:
                chat = client.chats.create(model=model_name)
                response = chat.send_message(prompt)
                result_text = response.text.strip()
                
                print(f"\n[Xử lý bởi {model_name}]")
                print(result_text)
                print("-" * 30)
                return result_text
                
            except Exception as e:
                print(f"⚠️ Node {model_name} thất bại. Lỗi chi tiết: {e}")
                continue
        
        print("❌ Tất cả các máy chủ đều đang quá tải cục bộ. Bạn hãy đợi khoảng 1 phút rồi thử lại nhé.")
        return None
        
    except Exception as e:
        print(f"❌ Lỗi hệ thống: {e}")
        return None

if __name__ == "__main__":
    GOOGLE_API_KEY = "AQ.Ab8RN6Ki7n2gR3a8huEtJmQ9wXMUiGdhN8cvIoQjUzcaqZeErQ"
    
    audio_file = record_audio(duration=5)
    english_text = transcribe_audio(audio_file)
    
    if english_text:
        translate_to_vietnamese(english_text, GOOGLE_API_KEY)