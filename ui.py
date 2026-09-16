from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QApplication, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor, QFont

class TranslationPopup(QWidget):
    save_vocab_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 8px; }
            QLabel { font-weight: bold; color: #333333; border: none; }
            QLabel#phoneticsLabel { font-weight: normal; color: #7f8c8d; font-style: italic; font-size: 12px; }
            QLabel#exampleLabel  { font-weight: normal; color: #555555; font-size: 11px; }
            QTextEdit { border: none; background-color: #f9f9f9; color: #2c3e50; }
            QPushButton#starButton {
                background-color: transparent;
                border: none;
                font-size: 20px;
                color: #bdc3c7;
            }
            QPushButton#starButton:hover { color: #f1c40f; }
            QPushButton#starButton.saved { color: #f1c40f; }
            QPushButton#closeButton {
                background-color: transparent;
                border: none;
                font-size: 15px;
                color: #aaaaaa;
                padding: 0px 4px;
            }
            QPushButton#closeButton:hover { color: #e74c3c; }
            QPushButton#historyButton {
                background-color: transparent;
                border: none;
                font-size: 15px;
                color: #7f8c8d;
                padding: 0px 2px;
            }
            QPushButton#historyButton:hover { color: #3498db; }
            QScrollBar:vertical { width: 6px; background: transparent; }
            QScrollBar::handle:vertical { background: #cccccc; border-radius: 3px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 15)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        self.lbl_translated = QLabel("Bản dịch:")
        self.btn_star = QPushButton("⭐")
        self.btn_star.setObjectName("starButton")
        self.btn_star.setToolTip("Lưu vào sổ tay")
        self.btn_star.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_star.clicked.connect(self.on_star_clicked)

        self.btn_history = QPushButton("📚")
        self.btn_history.setObjectName("historyButton")
        self.btn_history.setToolTip("Xem sổ tay từ vựng")
        self.btn_history.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("closeButton")
        self.btn_close.setToolTip("Đóng (Esc)")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.hide)
        header_layout.addWidget(self.lbl_translated)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_star)
        header_layout.addWidget(self.btn_history)
        header_layout.addWidget(self.btn_close)

        self.txt_translated = QTextEdit()
        self.txt_translated.setReadOnly(True)
        self.txt_translated.setFont(QFont("Arial", 11))
        self.txt_translated.setMinimumHeight(50)
        self.txt_translated.setMaximumHeight(300)
        self.txt_translated.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.txt_translated.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.lbl_phonetics = QLabel("")
        self.lbl_phonetics.setObjectName("phoneticsLabel")
        self.lbl_phonetics.setVisible(False)

        self.lbl_example_title = QLabel("Ví dụ:")
        self.lbl_example_title.setVisible(False)
        self.lbl_example = QLabel("")
        self.lbl_example.setObjectName("exampleLabel")
        self.lbl_example.setWordWrap(True)
        self.lbl_example.setVisible(False)

        self.lbl_original = QLabel("Bản gốc:")
        self.txt_original = QTextEdit()
        self.txt_original.setReadOnly(True)
        self.txt_original.setFont(QFont("Arial", 10))
        self.txt_original.setFixedHeight(40)
        self.txt_original.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        layout.addLayout(header_layout)
        layout.addWidget(self.txt_translated)
        layout.addWidget(self.lbl_phonetics)
        layout.addWidget(self.lbl_example_title)
        layout.addWidget(self.lbl_example)
        layout.addSpacing(4)
        layout.addWidget(self.lbl_original)
        layout.addWidget(self.txt_original)

        self.setLayout(layout)
        self.setMinimumWidth(380)
        self.setMaximumWidth(380)

    def _auto_resize_translated(self):
        doc_height = int(self.txt_translated.document().size().height()) + 10
        clamped = max(50, min(doc_height, 300))
        self.txt_translated.setFixedHeight(clamped)

    def _parse_and_display(self, translated_text: str):
        if "Phiên âm:" in translated_text and "|" in translated_text:
            parts = translated_text.split("|")
            meaning = phonetics = example = ""
            for part in parts:
                part = part.strip()
                if part.startswith("Dịch:"):
                    meaning = part.replace("Dịch:", "").strip()
                elif part.startswith("Phiên âm:"):
                    phonetics = part.replace("Phiên âm:", "").strip()
                elif part.startswith("Ví dụ:"):
                    example = part.replace("Ví dụ:", "").strip()

            self.txt_translated.setText(meaning)
            self.lbl_phonetics.setText(f"🔊 {phonetics}" if phonetics else "")
            self.lbl_phonetics.setVisible(bool(phonetics))
            self.lbl_example_title.setVisible(bool(example))
            self.lbl_example.setText(example)
            self.lbl_example.setVisible(bool(example))
        else:
            self.txt_translated.setText(translated_text)
            self.lbl_phonetics.setVisible(False)
            self.lbl_example_title.setVisible(False)
            self.lbl_example.setVisible(False)

        self._auto_resize_translated()
        self.adjustSize()

    def show_translation_at(self, original_text: str, translated_text: str, x: int, y: int):
        self.txt_original.setText(original_text)
        self._parse_and_display(translated_text)
        self._reset_star_button()

        screen = QApplication.primaryScreen().geometry()
        pos_x = x + 10
        pos_y = y - self.height() - 10

        if pos_y < 0:
            pos_y = y + 20
        if pos_x + self.width() > screen.width():
            pos_x = x - self.width() - 10

        self.move(pos_x, pos_y)
        self.show()
        self.activateWindow()

    def show_translation(self, original_text: str, translated_text: str):
        cursor_pos = QCursor.pos()
        self.show_translation_at(original_text, translated_text, cursor_pos.x(), cursor_pos.y())

    def on_star_clicked(self):
        orig      = self.txt_original.toPlainText().strip()
        trans     = self.txt_translated.toPlainText().strip()
        phonetics = self.lbl_phonetics.text().replace("🔊 ", "").strip()
        example   = self.lbl_example.text().strip()

        full = f"Dịch: {trans}"
        if phonetics:
            full += f" | Phiên âm: {phonetics}"
        if example:
            full += f" | Ví dụ: {example}"

        if not orig or not trans:
            self.btn_star.setToolTip("Không thể lưu!")
            self.btn_star.setStyleSheet("color: #e74c3c;")
            QTimer.singleShot(1000, self._reset_star_button)
            return

        self.btn_star.setProperty("class", "saved")
        self.style().unpolish(self.btn_star)
        self.style().polish(self.btn_star)
        self.btn_star.setToolTip("Đã lưu vào sổ tay ✓")
        self.save_vocab_signal.emit(orig, full)

    def _reset_star_button(self):
        self.btn_star.setProperty("class", "")
        self.style().unpolish(self.btn_star)
        self.style().polish(self.btn_star)
        self.btn_star.setStyleSheet("")
        self.btn_star.setToolTip("Lưu vào sổ tay")

    def wheelEvent(self, event):
        """Lăn chuột → popup di chuyển theo trục Y"""
        delta = event.angleDelta().y()
        step = 60  
        current = self.pos()
        if delta > 0:
            self.move(current.x(), current.y() - step)  
        else:
            self.move(current.x(), current.y() + step)  

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()