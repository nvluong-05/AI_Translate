import webbrowser
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QProgressBar,
    QWidget, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from youtube_translate import YouTubeTranslator, parse_srt


class SubtitlePanel(QWidget):
    """Panel hiện phụ đề đồng bộ — dùng QTimer tick mỗi 300ms"""

    def __init__(self):
        super().__init__()
        self.entries   = []   
        self.current   = -1
        self._timer    = QTimer()
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._tick)
        self._elapsed  = 0.0  
        self._playing  = False
        self._play_start_wall = 0.0
        self._play_start_elapsed = 0.0
        self._line_widgets = []
        self._build_ui()

    def _build_ui(self):
        self.setMinimumWidth(320)
        self.setMaximumWidth(420)
        self.setStyleSheet("""
            QWidget { background: #111111; }
            QLabel#header {
                font-size: 13px; font-weight: bold; color: #ffffff;
                background: #1a1a1a; padding: 10px 14px;
                border-bottom: 1px solid #333;
            }
            QLabel#time {
                font-size: 11px; color: #888;
                background: #1a1a1a; padding: 4px 14px 8px 14px;
            }
            QLabel#hint {
                font-size: 11px; color: #666;
                padding: 6px 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.lbl_header = QLabel("📝 Phụ đề tiếng Việt")
        self.lbl_header.setObjectName("header")
        layout.addWidget(self.lbl_header)

        self.lbl_time = QLabel("⏱ 00:00")
        self.lbl_time.setObjectName("time")
        layout.addWidget(self.lbl_time)

        ctrl = QWidget()
        ctrl.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid #333;")
        ctrl_layout = QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(10, 6, 10, 6)
        ctrl_layout.setSpacing(6)

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setFixedHeight(28)
        self.btn_play.setStyleSheet("""
            QPushButton { background: #e74c3c; color: white; border: none;
                          border-radius: 4px; font-size: 12px; padding: 0 12px; }
            QPushButton:hover { background: #c0392b; }
        """)
        self.btn_play.clicked.connect(self._on_play)

        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setFixedHeight(28)
        self.btn_pause.setStyleSheet("""
            QPushButton { background: #555; color: white; border: none;
                          border-radius: 4px; font-size: 12px; padding: 0 12px; }
            QPushButton:hover { background: #777; }
        """)
        self.btn_pause.clicked.connect(self._on_pause)

        self.btn_reset = QPushButton("↺ Reset")
        self.btn_reset.setFixedHeight(28)
        self.btn_reset.setStyleSheet("""
            QPushButton { background: #333; color: #aaa; border: none;
                          border-radius: 4px; font-size: 12px; padding: 0 12px; }
            QPushButton:hover { background: #444; }
        """)
        self.btn_reset.clicked.connect(self._on_reset)

        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(self.btn_pause)
        ctrl_layout.addWidget(self.btn_reset)
        ctrl_layout.addStretch()
        layout.addWidget(ctrl)

        hint = QLabel("💡 Nhấn Play cùng lúc với video YouTube")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: #111; }
            QScrollBar:vertical { width: 4px; background: transparent; }
            QScrollBar::handle:vertical { background: #444; border-radius: 2px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self.lines_widget = QWidget()
        self.lines_widget.setStyleSheet("background: #111111;")
        self.lines_layout = QVBoxLayout(self.lines_widget)
        self.lines_layout.setContentsMargins(8, 8, 8, 8)
        self.lines_layout.setSpacing(2)
        self.lines_layout.addStretch()

        self.scroll.setWidget(self.lines_widget)
        layout.addWidget(self.scroll)

    def load_srt(self, srt_content: str):
        """Load SRT tiếng Việt và tạo widget cho từng dòng"""
        for w in self._line_widgets:
            w.deleteLater()
        self._line_widgets.clear()

        while self.lines_layout.count() > 1:
            item = self.lines_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = parse_srt(srt_content)
        self.entries = []

        for e in entries:
            try:
                start_sec = self._ts_to_sec(e["times"].split("-->")[0].strip())
                end_sec   = self._ts_to_sec(e["times"].split("-->")[1].strip())
            except Exception:
                continue
            self.entries.append({**e, "start_sec": start_sec, "end_sec": end_sec})

            lbl = QLabel(e["text"])
            lbl.setWordWrap(True)
            lbl.setFont(QFont("Arial", 12))
            lbl.setStyleSheet("""
                QLabel {
                    color: #bbbbbb; background: transparent;
                    padding: 5px 10px; border-radius: 4px;
                    border-left: 3px solid transparent;
                }
            """)
            self.lines_layout.insertWidget(self.lines_layout.count() - 1, lbl)
            self._line_widgets.append(lbl)

        self.current = -1
        self._elapsed = 0.0

    def _ts_to_sec(self, ts: str) -> float:
        ts = ts.replace(",", ".")
        parts = ts.strip().split(":")
        h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + s

    def _on_play(self):
        self._play_start_wall = time.time()
        self._play_start_elapsed = self._elapsed
        self._playing = True
        self._timer.start()

    def _on_pause(self):
        if self._playing:
            self._elapsed = self._play_start_elapsed + (time.time() - self._play_start_wall)
        self._playing = False
        self._timer.stop()

    def _on_reset(self):
        self._timer.stop()
        self._playing = False
        self._elapsed = 0.0
        self.lbl_time.setText("⏱ 00:00")
        self._highlight(-1)

    def _tick(self):
        if not self._playing:
            return
        self._elapsed = self._play_start_elapsed + (time.time() - self._play_start_wall)

        total = int(self._elapsed)
        m, s  = divmod(total, 60)
        self.lbl_time.setText(f"⏱ {m:02d}:{s:02d}")

        found = -1
        for i, e in enumerate(self.entries):
            if e["start_sec"] <= self._elapsed <= e["end_sec"]:
                found = i
                break

        if found != self.current:
            self._highlight(found)

    def _highlight(self, idx: int):
        if 0 <= self.current < len(self._line_widgets):
            self._line_widgets[self.current].setStyleSheet("""
                QLabel { color: #bbbbbb; background: transparent;
                         padding: 5px 10px; border-radius: 4px;
                         border-left: 3px solid transparent; }
            """)
        self.current = idx
        if 0 <= self.current < len(self._line_widgets):
            self._line_widgets[self.current].setStyleSheet("""
                QLabel { color: #ffffff; background: #2a2a2a;
                         padding: 5px 10px; border-radius: 4px;
                         border-left: 3px solid #ff0000; font-weight: bold; }
            """)
            self.scroll.ensureWidgetVisible(self._line_widgets[self.current])


class YouTubeDialog(QDialog):
    def __init__(self, api_key: str, parent=None):
        super().__init__(parent)
        self.api_key    = api_key
        self.translator = YouTubeTranslator(api_key)
        from PyQt6.QtCore import Qt
        self.translator.progress.connect(self._on_progress, Qt.ConnectionType.QueuedConnection)
        self.translator.finished.connect(self._on_finished, Qt.ConnectionType.QueuedConnection)
        self.translator.error.connect(self._on_error, Qt.ConnectionType.QueuedConnection)
        self.setWindowTitle("🎬 Dịch video YouTube")
        self.setMinimumSize(380, 600)
        self.resize(380, 700)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Window
        )
        self._srt_content = ""
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog { background: #111111; }
            QLabel { border: none; color: #ffffff; }
            QLabel#title { font-size: 14px; font-weight: bold; color: #fff; }
            QLabel#hint  { font-size: 11px; color: #888; }
            QLabel#status { font-size: 11px; color: #aaa; }
            QLineEdit {
                border: 1px solid #333; border-radius: 6px;
                padding: 8px 12px; font-size: 12px;
                background: #1a1a1a; color: white;
            }
            QPushButton#btnGo {
                background: #e74c3c; color: white; border: none;
                border-radius: 6px; padding: 8px 16px; font-size: 12px; font-weight: bold;
            }
            QPushButton#btnGo:hover { background: #c0392b; }
            QPushButton#btnGo:disabled { background: #444; color: #888; }
            QPushButton#btnOpen {
                background: #2980b9; color: white; border: none;
                border-radius: 6px; padding: 8px 16px; font-size: 12px;
            }
            QPushButton#btnOpen:hover { background: #1a6699; }
            QPushButton#btnOpen:disabled { background: #444; color: #888; }
            QProgressBar {
                border: none; border-radius: 3px;
                background: #333; height: 4px;
            }
            QProgressBar::chunk { background: #e74c3c; border-radius: 3px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        lbl_title = QLabel("🎬 Dịch video YouTube")
        lbl_title.setObjectName("title")
        layout.addWidget(lbl_title)

        lbl_hint = QLabel("Dán link YouTube:")
        lbl_hint.setObjectName("hint")
        layout.addWidget(lbl_hint)

        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.input_url.returnPressed.connect(self._start)
        layout.addWidget(self.input_url)

        btn_row = QHBoxLayout()
        self.btn_go = QPushButton("▶ Lấy phụ đề")
        self.btn_go.setObjectName("btnGo")
        self.btn_go.clicked.connect(self._start)

        self.btn_open = QPushButton("🌐 Mở YouTube")
        self.btn_open.setObjectName("btnOpen")
        self.btn_open.clicked.connect(self._open_youtube)
        self.btn_open.setEnabled(False)

        btn_row.addWidget(self.btn_go)
        btn_row.addWidget(self.btn_open)
        layout.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setObjectName("status")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #333;")
        layout.addWidget(line)

        self.sub_panel = SubtitlePanel()
        layout.addWidget(self.sub_panel)

    def _start(self):
        url = self.input_url.text().strip()
        if "youtube.com" not in url and "youtu.be" not in url:
            self.lbl_status.setText("⚠️ Vui lòng nhập link YouTube hợp lệ.")
            return
        self.btn_go.setEnabled(False)
        self.btn_open.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText("Đang xử lý...")
        self.translator.translate_async(url)

    def _open_youtube(self):
        url = self.input_url.text().strip()
        if url:
            webbrowser.open(url)
            self.lbl_status.setText("✅ Đã mở YouTube — nhấn ▶ Play để đồng bộ phụ đề!")

    def _on_progress(self, msg: str):
        self.lbl_status.setText(msg)

    def _on_finished(self, srt_path: str):
        """Nhận path file SRT thay vì HTML"""
        self.progress_bar.setVisible(False)
        self.btn_go.setEnabled(True)
        self.btn_open.setEnabled(True)

        try:
            from pathlib import Path
            p = Path(srt_path)
            print(f"SRT path: {p}")
            print(f"File exists: {p.exists()}")
            srt_content = Path(srt_path).read_text(encoding="utf-8")
            print(f"SRT lines: {len(srt_content.splitlines())}")
            self.sub_panel.load_srt(srt_content)
            self.lbl_status.setText(
                "✅ Xong! Nhấn '🌐 Mở YouTube' → play video → nhấn ▶ Play để đồng bộ phụ đề."
            )
        except Exception as e:
            self.lbl_status.setText(f"❌ Lỗi load phụ đề: {e}")

    def _on_error(self, msg: str):
        self.progress_bar.setVisible(False)
        self.btn_go.setEnabled(True)
        self.lbl_status.setText(msg)