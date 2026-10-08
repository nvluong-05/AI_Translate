import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt
from youtube_translate import YouTubeTranslator


class YouTubeDialog(QDialog):
    def __init__(self, api_key: str, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.translator = YouTubeTranslator(api_key)
        self.translator.progress.connect(self._on_progress)
        self.translator.finished.connect(self._on_finished)
        self.translator.error.connect(self._on_error)
        self.setWindowTitle("🎬 Dịch video YouTube")
        self.setFixedWidth(480)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog { background: #f5f6fa; }
            QLabel { border: none; color: #2c3e50; }
            QLabel#title { font-size: 15px; font-weight: bold; }
            QLabel#hint  { font-size: 12px; color: #7f8c8d; }
            QLabel#note  { font-size: 11px; color: #27ae60; background: #eafaf1;
                           border-radius: 4px; padding: 6px 8px; }
            QLabel#status { font-size: 12px; color: #2c3e50; }
            QLineEdit {
                border: 1px solid #dcdde1; border-radius: 6px;
                padding: 8px 12px; font-size: 13px; background: white;
            }
            QPushButton#btnGo {
                background: #e74c3c; color: white; border: none;
                border-radius: 6px; padding: 9px 20px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton#btnGo:hover { background: #c0392b; }
            QPushButton#btnGo:disabled { background: #bdc3c7; }
            QPushButton#btnCancel {
                background: transparent; color: #7f8c8d;
                border: 1px solid #dcdde1; border-radius: 6px;
                padding: 9px 16px; font-size: 13px;
            }
            QPushButton#btnCancel:hover { background: #dcdde1; }
            QProgressBar {
                border: none; border-radius: 4px;
                background: #dcdde1; height: 6px;
            }
            QProgressBar::chunk { background: #e74c3c; border-radius: 4px; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        lbl_title = QLabel("🎬 Dịch video YouTube sang tiếng Việt")
        lbl_title.setObjectName("title")

        lbl_hint = QLabel("Dán link video YouTube (có hoặc không có phụ đề):")
        lbl_hint.setObjectName("hint")

        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.input_url.returnPressed.connect(self._start)

        # Ghi chú cho người dùng
        lbl_note = QLabel(
            "✅ Có phụ đề CC → dịch nhanh (vài giây)\n"
            "🎙️ Không có phụ đề → dùng Whisper nhận diện (lâu hơn, lần đầu tải model ~150MB)"
        )
        lbl_note.setObjectName("note")
        lbl_note.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)

        self.lbl_status = QLabel("")
        self.lbl_status.setObjectName("status")
        self.lbl_status.setWordWrap(True)

        btn_row = QHBoxLayout()
        self.btn_go = QPushButton("▶ Dịch ngay")
        self.btn_go.setObjectName("btnGo")
        self.btn_go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_go.clicked.connect(self._start)

        btn_cancel = QPushButton("Đóng")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.close)

        btn_row.addWidget(self.btn_go)
        btn_row.addWidget(btn_cancel)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_hint)
        layout.addWidget(self.input_url)
        layout.addWidget(lbl_note)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.lbl_status)
        layout.addLayout(btn_row)
        self.setLayout(layout)

    def _start(self):
        url = self.input_url.text().strip()
        if "youtube.com" not in url and "youtu.be" not in url:
            self.lbl_status.setText("⚠️ Vui lòng nhập link YouTube hợp lệ.")
            return
        self.btn_go.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText("Đang xử lý...")
        self.translator.translate_async(url)

    def _on_progress(self, msg: str):
        self.lbl_status.setText(msg)

    def _on_finished(self, html_path: str):
        self.progress_bar.setVisible(False)
        self.btn_go.setEnabled(True)
        self.lbl_status.setText("✅ Xong! Đang mở trình phát...")
        webbrowser.open(f"file:///{html_path.replace(chr(92), '/')}")

    def _on_error(self, msg: str):
        self.progress_bar.setVisible(False)
        self.btn_go.setEnabled(True)
        self.lbl_status.setText(msg)