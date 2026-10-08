import os
import re
import time
import requests
import threading
import subprocess
import shutil
from pathlib import Path
from dotenv import load_dotenv
from PyQt6.QtCore import QObject, pyqtSignal

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS = [
    "google/gemini-2.0-flash-lite",
    "meta-llama/llama-3.3-70b-instruct",
    "openrouter/auto",
]

OUTPUT_DIR = Path(os.environ.get("APPDATA", Path.home())) / "AI_Translate" / "subtitles"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _call_api(prompt: str, api_key: str) -> str | None:
    for model in MODELS:
        try:
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
                timeout=30,
            )
            data = response.json()
            if "error" in data:
                continue
            choices = data.get("choices", [])
            if not choices:
                continue
            content = choices[0].get("message", {}).get("content", "")
            if content:
                return content.strip()
        except Exception:
            continue
    return None


def parse_srt(srt_content: str) -> list[dict]:
    blocks = re.split(r'\n\s*\n', srt_content.strip())
    entries = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        try:
            index = int(lines[0].strip())
            times = lines[1].strip()
            text  = " ".join(lines[2:]).strip()
            text  = re.sub(r'<[^>]+>', '', text).strip()
            if text:
                entries.append({"index": index, "times": times, "text": text})
        except ValueError:
            continue
    return entries


def build_srt(entries: list[dict]) -> str:
    return "\n\n".join(f"{e['index']}\n{e['times']}\n{e['text']}" for e in entries)


def translate_batch(lines: list[str], api_key: str) -> list[str]:
    if not lines:
        return []
    numbered = "\n".join(f"{i+1}. {line}" for i, line in enumerate(lines))
    prompt = f"""Translate these subtitle lines to Vietnamese.
Return EXACTLY the same number of lines, each as: [number]. [translation]
No explanations, keep it natural and concise.

{numbered}"""
    result = _call_api(prompt, api_key)
    if not result:
        return lines
    translated = []
    for line in result.splitlines():
        m = re.match(r'^\d+\.\s*(.+)$', line.strip())
        if m:
            translated.append(m.group(1).strip())
    while len(translated) < len(lines):
        translated.append(lines[len(translated)])
    return translated[:len(lines)]


def srt_to_vtt(srt_content: str) -> str:
    vtt = "WEBVTT\n\n"
    entries = parse_srt(srt_content)
    for e in entries:
        times = e["times"].replace(",", ".")
        vtt += f"{times}\n{e['text']}\n\n"
    return vtt


def build_html_player(youtube_url: str, vtt_content: str, srt_vi_path: Path) -> str:
    match = re.search(r'(?:v=|youtu\.be/)([^&\n?#]+)', youtube_url)
    video_id = match.group(1) if match else ""
    vtt_escaped = vtt_content.replace('`', r'\`')
    html_path = srt_vi_path.with_suffix(".html")
    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Translate — YouTube Player</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0d0d0d; color: #fff; font-family: Arial, sans-serif; height: 100vh; overflow: hidden; }}

  /* Layout 2 cột */
  .container {{
    display: flex;
    height: 100vh;
    gap: 0;
  }}

  /* Cột trái: video */
  .video-col {{
    flex: 1 1 65%;
    display: flex;
    flex-direction: column;
    background: #000;
    padding: 12px;
    gap: 8px;
    min-width: 0;
  }}
  .video-title {{
    font-size: 12px;
    color: #888;
    flex-shrink: 0;
  }}
  #frame {{
    width: 100%;
    flex: 1;
    border-radius: 8px;
    background: #111;
    border: none;
  }}

  /* Cột phải: phụ đề */
  .sub-col {{
    flex: 0 0 35%;
    display: flex;
    flex-direction: column;
    background: #141414;
    border-left: 1px solid #222;
    min-width: 280px;
    max-width: 420px;
  }}
  .sub-header {{
    padding: 12px 16px;
    font-size: 12px;
    font-weight: bold;
    color: #bbb;
    border-bottom: 1px solid #222;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .sub-header span.dot {{
    width: 8px; height: 8px;
    background: #ff0000;
    border-radius: 50%;
    display: inline-block;
  }}
  .sub-list {{
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }}
  .sub-list::-webkit-scrollbar {{ width: 4px; }}
  .sub-list::-webkit-scrollbar-track {{ background: transparent; }}
  .sub-list::-webkit-scrollbar-thumb {{ background: #333; border-radius: 2px; }}

  .sub-line {{
    padding: 8px 10px;
    border-radius: 6px;
    font-size: 13px;
    line-height: 1.6;
    color: #888;
    border-left: 3px solid transparent;
    margin-bottom: 2px;
    transition: all 0.15s ease;
  }}
  .sub-line.active {{
    background: #1e1e1e;
    border-left-color: #ff0000;
    color: #ffffff;
    font-weight: 500;
  }}
  .sub-footer {{
    padding: 8px 16px;
    font-size: 10px;
    color: #444;
    border-top: 1px solid #222;
    flex-shrink: 0;
  }}
</style>
</head>
<body>
<div class="container">
  <!-- Cột trái: Video -->
  <div class="video-col">
    <div class="video-title">🎬 AI Translate — Phụ đề tiếng Việt</div>
    <iframe id="frame"
      src="https://www.youtube.com/embed/{video_id}?enablejsapi=1"
      frameborder="0" allowfullscreen allow="autoplay">
    </iframe>
  </div>

  <!-- Cột phải: Phụ đề -->
  <div class="sub-col">
    <div class="sub-header">
      <span class="dot"></span>
      Phụ đề tiếng Việt
    </div>
    <div class="sub-list" id="subList">
      <div id="lines"></div>
    </div>
    <div class="sub-footer">Tắt CC gốc trên YouTube để tránh chồng phụ đề</div>
  </div>
</div>
<script>
const vttRaw = `{vtt_escaped}`;
function parseVTT(raw) {{
  const blocks = raw.trim().split(/\\n\\s*\\n/).slice(1);
  return blocks.map(b => {{
    const lines = b.trim().split('\\n');
    if (lines.length < 2) return null;
    const [start, end] = lines[0].split(' --> ').map(toSec);
    const text = lines.slice(1).join(' ');
    return {{ start, end, text }};
  }}).filter(Boolean);
}}
function toSec(t) {{
  const [h, m, s] = t.trim().split(':');
  return parseFloat(h)*3600 + parseFloat(m)*60 + parseFloat(s);
}}
const subs = parseVTT(vttRaw);
const linesEl = document.getElementById('lines');
subs.forEach((s, i) => {{
  const d = document.createElement('div');
  d.className = 'sub-line'; d.id = 'sub-' + i; d.textContent = s.text;
  linesEl.appendChild(d);
}});
let player, currentIdx = -1;
function onYTReady() {{
  player = new YT.Player('frame', {{ events: {{ onReady: () => setInterval(tick, 300) }} }});
}}
window.onYouTubeIframeAPIReady = onYTReady;
function tick() {{
  if (!player || !player.getCurrentTime) return;
  const t = player.getCurrentTime();
  let found = -1;
  for (let i = 0; i < subs.length; i++) {{
    if (t >= subs[i].start && t <= subs[i].end) {{ found = i; break; }}
  }}
  if (found !== currentIdx) {{
    if (currentIdx >= 0) document.getElementById('sub-' + currentIdx)?.classList.remove('active');
    currentIdx = found;
    if (currentIdx >= 0) {{
      const el = document.getElementById('sub-' + currentIdx);
      el?.classList.add('active');
      el?.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
    }}
  }}
}}
</script>
<script src="https://www.youtube.com/iframe_api"></script>
</body>
</html>"""
    html_path.write_text(html, encoding="utf-8")
    return str(html_path)


def _whisper_transcribe(audio_path: Path, progress_cb) -> list[dict]:
    """Dùng Whisper nhận diện giọng nói → trả về entries SRT"""
    try:
        import whisper
        progress_cb("🎙️ Đang tải Whisper model (lần đầu có thể lâu)...")
        model = whisper.load_model("base")
        progress_cb("🎙️ Đang nhận diện giọng nói bằng Whisper...")
        result = model.transcribe(str(audio_path), task="transcribe")
        entries = []
        for i, seg in enumerate(result.get("segments", []), 1):
            start = seg["start"]
            end   = seg["end"]
            text  = seg["text"].strip()
            if not text:
                continue
            def to_ts(sec):
                h = int(sec // 3600)
                m = int((sec % 3600) // 60)
                s = int(sec % 60)
                ms = int((sec - int(sec)) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            times = f"{to_ts(start)} --> {to_ts(end)}"
            entries.append({"index": i, "times": times, "text": text})
        return entries
    except ImportError:
        raise RuntimeError("Whisper chưa được cài. Chạy: pip install openai-whisper")
    except Exception as e:
        raise RuntimeError(f"Lỗi Whisper: {e}")


class YouTubeTranslator(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    def translate_async(self, youtube_url: str):
        t = threading.Thread(target=self._run, args=(youtube_url,), daemon=True)
        t.start()

    def _run(self, youtube_url: str):
        if not shutil.which("yt-dlp"):
            self.error.emit("❌ Cần cài yt-dlp:\npip install yt-dlp")
            return

        match = re.search(r'(?:v=|youtu\.be/)([^&\n?#]+)', youtube_url)
        if not match:
            self.error.emit("❌ Link YouTube không hợp lệ.")
            return
        video_id = match.group(1)

        srt_vi_path = OUTPUT_DIR / f"{video_id}_vi.srt"
        entries = []

        self.progress.emit("🔍 Đang tìm phụ đề từ YouTube...")
        out_template = str(OUTPUT_DIR / f"{video_id}.%(ext)s")
        subprocess.run([
            "yt-dlp",
            "--write-sub", "--write-auto-sub",
            "--sub-lang", "en",
            "--sub-format", "srt",
            "--skip-download",
            "--output", out_template,
            youtube_url
        ], capture_output=True, text=True, timeout=60)

        srt_files = sorted(OUTPUT_DIR.glob(f"{video_id}*.srt"))
        if srt_files:
            self.progress.emit("✅ Tìm thấy phụ đề gốc, đang xử lý...")
            srt_content = srt_files[0].read_text(encoding="utf-8", errors="ignore")
            entries = parse_srt(srt_content)

        if not entries:
            self.progress.emit("⚠️ Không có phụ đề CC. Đang tải audio để dùng Whisper...")
            audio_path = OUTPUT_DIR / f"{video_id}.mp3"
            try:
                subprocess.run([
                    "yt-dlp",
                    "--extract-audio",
                    "--audio-format", "mp3",
                    "--audio-quality", "0",
                    "--output", str(audio_path),
                    youtube_url
                ], capture_output=True, text=True, timeout=300, check=True)

                if not audio_path.exists():
                    self.error.emit("❌ Không tải được audio từ video.")
                    return

                entries = _whisper_transcribe(audio_path, self.progress.emit)
                audio_path.unlink(missing_ok=True)

            except subprocess.CalledProcessError:
                self.error.emit("❌ Không thể tải audio. Kiểm tra kết nối mạng.")
                return
            except RuntimeError as e:
                self.error.emit(str(e))
                return

        if not entries:
            self.error.emit("❌ Không nhận diện được nội dung từ video.")
            return

        total = len(entries)
        self.progress.emit(f"🌐 Đang dịch {total} dòng phụ đề...")

        BATCH = 15
        texts = [e["text"] for e in entries]
        translated = []

        for i in range(0, total, BATCH):
            batch = texts[i:i+BATCH]
            result_batch = translate_batch(batch, self.api_key)
            translated.extend(result_batch)
            done = min(i + BATCH, total)
            self.progress.emit(f"🌐 Đã dịch {done}/{total} dòng...")
            time.sleep(0.3)

        for i, entry in enumerate(entries):
            entry["text"] = translated[i] if i < len(translated) else entry["text"]

        srt_vi = build_srt(entries)
        srt_vi_path.write_text(srt_vi, encoding="utf-8")

        self.finished.emit(str(srt_vi_path))