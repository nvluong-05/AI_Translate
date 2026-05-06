from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QApplication, QPushButton
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
            QTextEdit { border: none; background-color: #f9f9f9; color: #2c3e50; }
            /* Style riêng cho nút Ngôi sao */
            QPushButton#starButton {
                background-color: transparent;
                border: none;
                font-size: 20px;
                color: #bdc3c7; /* Màu xám khi chưa lưu */
                transition: color 0.3s ease;
            }
            QPushButton#starButton:hover { color: #f1c40f; /* Màu vàng khi hover */ }
            QPushButton#starButton.saved { color: #f1c40f; /* Màu vàng khi đã lưu */ }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        # 2. Xây dựng khu vực Header (Chứa nhãn và Nút Ngôi sao)
        header_layout = QHBoxLayout()
        self.lbl_translated = QLabel("Bản dịch:")
        
        self.btn_star = QPushButton("⭐")
        self.btn_star.setObjectName("starButton") # Đặt ID để áp dụng CSS
        self.btn_star.setToolTip("Lưu vào sổ tay")
        self.btn_star.setCursor(Qt.CursorShape.PointingHandCursor)
        # Bắt sự kiện click
        self.btn_star.clicked.connect(self.on_star_clicked)

        header_layout.addWidget(self.lbl_translated)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_star)

        self.txt_translated = QTextEdit()
        self.txt_translated.setReadOnly(True)
        self.txt_translated.setFont(QFont("Arial", 11))

        self.lbl_original = QLabel("Bản gốc:")
        self.txt_original = QTextEdit()
        self.txt_original.setReadOnly(True)
        self.txt_original.setFont(QFont("Arial", 10))
        self.txt_original.setMaximumHeight(60)

        # Gộp tất cả vào Layout chính
        layout.addLayout(header_layout)
        layout.addWidget(self.txt_translated)
        layout.addWidget(self.lbl_original)
        layout.addWidget(self.txt_original)

        self.setLayout(layout)
        self.resize(400, 280)

    def show_translation(self, original_text, translated_text):
        self.txt_original.setText(original_text)
        self.txt_translated.setText(translated_text)
        
        self.btn_star.setProperty("class", "")
        self.style().unpolish(self.btn_star)
        self.style().polish(self.btn_star)

        cursor_pos = QCursor.pos()
        offset_x, offset_y = 15, 15
        
        screen_geometry = self.screen().geometry()
        if cursor_pos.x() + offset_x + self.width() > screen_geometry.width():
            offset_x = -self.width() - 15
        if cursor_pos.y() + offset_y + self.height() > screen_geometry.height():
            offset_y = -self.height() - 15
            
        self.move(cursor_pos.x() + offset_x, cursor_pos.y() + offset_y)
        self.show()
        self.activateWindow()

    def on_star_clicked(self):
        """Hàm xử lý khi người dùng bấm vào Ngôi sao"""
        orig = self.txt_original.toPlainText().strip()
        trans = self.txt_translated.toPlainText().strip()
        
        if not orig or not trans:
            self.btn_star.setToolTip("Không thể lưu: Text không được để trống")
            self.btn_star.setStyleSheet("color: #e74c3c;")
            QTimer.singleShot(1000, self._reset_star_button)
            return
        
        self.btn_star.setProperty("class", "saved")
        self.style().unpolish(self.btn_star)
        self.style().polish(self.btn_star)
        self.btn_star.setToolTip("Đã lưu vào sổ tay ✓")
        
        self.save_vocab_signal.emit(orig, trans)
    
    def _reset_star_button(self):
        """Reset nút star về trạng thái ban đầu"""
        self.btn_star.setProperty("class", "")
        self.style().unpolish(self.btn_star)
        self.style().polish(self.btn_star)
        self.btn_star.setToolTip("Lưu vào sổ tay")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()