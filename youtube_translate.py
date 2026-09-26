import os
import re
import time
import requests
import threading
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

OUTPUT_DIR = Path(os.environ.get("APPDATA" , Path.home())) / "AI_Translate" / "subtitles"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _call_api(prompt: str, api_key: str) -> str | None :
    for model in MODELS:
        try:
            respone =  requests.post(
                API_URL,
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
                timeout = 30
            )
            
            data =  respone.json()
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
    """Parse SRT thành list [{index, times, text}]"""
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
            text = re.sub(r'<[^>]+>', '', text).strip()
            if text:
                entries.append({"index": index, "times": times, "text": text})
        except ValueError:
            continue
    return entries

def build_srt(entries: list[dict]) -> str:
    return "\n\n".join(f"{e['index']}\n{e['times']}\n{e['text']}" for e in entries)
 
 
def translate_batch(lines: list[str], api_key: str) -> list[str]:
    """Dịch 1 batch dòng phụ đề"""
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
    """Convert SRT sang WebVTT cho HTML5"""
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
  body {{ background: #0f0f0f; color: #fff; font-family: Arial, sans-serif; }}
  .wrap {{ max-width: 860px; margin: 0 auto; padding: 16px; }}
  h2 {{ font-size: 14px; color: #aaa; margin-bottom: 10px; }}
  #frame {{ width: 100%; aspect-ratio: 16/9; border-radius: 8px; background: #000; }}
  .sub-box {{
    background: #1a1a1a; border-radius: 8px;
    margin-top: 12px; padding: 12px 16px;
    max-height: 260px; overflow-y: auto;
  }}
  .sub-line {{
    padding: 5px 8px; border-radius: 4px;
    font-size: 13px; line-height: 1.5; cursor: default;
    border-left: 3px solid transparent;
  }}
  .sub-line.active {{
    background: #2a2a2a;
    border-left-color: #ff0000;
    color: #fff;
  }}
  .note {{ color: #666; font-size: 11px; margin-top: 8px; }}
</style>
</head>
<body>
<div class="wrap">
  <h2>🎬 AI Translate — Phụ đề tiếng Việt</h2>
  <iframe id="frame"
    src="https://www.youtube.com/embed/{video_id}?enablejsapi=1"
    frameborder="0" allowfullscreen allow="autoplay">
  </iframe>
  <div class="sub-box" id="subBox">
    <div id="lines"></div>
  </div>
  <p class="note">💡 Tắt phụ đề gốc trên YouTube để đọc phụ đề tiếng Việt bên dưới.</p>
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
const subBox  = document.getElementById('subBox');
 
subs.forEach((s, i) => {{
  const d = document.createElement('div');
  d.className = 'sub-line';
  d.id = 'sub-' + i;
  d.textContent = s.text;
  linesEl.appendChild(d);
}});
 
let player, currentIdx = -1;
function onYTReady() {{
  player = new YT.Player('frame', {{
    events: {{ onReady: () => setInterval(tick, 300) }}
  }});
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
        import subprocess, shutil
 
        if not shutil.which("yt-dlp"):
            self.error.emit("❌ Cần cài yt-dlp:\n pip install yt-dlp")
            return
 
        match = re.search(r'(?:v=|youtu\.be/)([^&\n?#]+)', youtube_url)
        if not match:
            self.error.emit("❌ Link YouTube không hợp lệ.")
            return
        video_id = match.group(1)
 
        srt_vi_path = OUTPUT_DIR / f"{video_id}_vi.srt"
        html_path   = OUTPUT_DIR / f"{video_id}_player.html"
 
        self.progress.emit("🔍 Đang lấy phụ đề từ YouTube...")
 
        out_template = str(OUTPUT_DIR / f"{video_id}.%(ext)s")
        result = subprocess.run([
            "yt-dlp",
            "--write-sub", "--write-auto-sub",
            "--sub-lang", "en",
            "--sub-format", "srt",
            "--skip-download",
            "--output", out_template,
            youtube_url
        ], capture_output=True, text=True, timeout=60)
 
        srt_files = sorted(OUTPUT_DIR.glob(f"{video_id}*.srt"))
        if not srt_files:
            self.error.emit("❌ Video không có phụ đề tiếng Anh.\nHãy thử video khác có CC (phụ đề).")
            return
 
        srt_content = srt_files[0].read_text(encoding="utf-8", errors="ignore")
        entries = parse_srt(srt_content)
 
        if not entries:
            self.error.emit("❌ Không đọc được phụ đề từ video này.")
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
 
        self.progress.emit("✅ Đang tạo trình phát video...")
        vtt = srt_to_vtt(srt_vi)
        html_file = build_html_player(youtube_url, vtt, srt_vi_path)
 
        self.finished.emit(html_file)

            