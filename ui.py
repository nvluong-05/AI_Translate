from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QApplication, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor, QFont

class TranslationPopup(QWidget):
    # 1. Khởi tạo một "Tín hiệu" tùy chỉnh. 
    # Tín hiệu này sẽ mang theo 2 chuỗi (string): Bản gốc và Bản dịch.
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
        header_layout.addStretch() # Đẩy nút ngôi sao sát về bên phải
        header_layout.addWidget(self.btn_star)

        # Khởi tạo các vùng text
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
        # Responsive size dựa trên content
        self.resize(400, 280)

    def show_translation(self, original_text, translated_text):
        self.txt_original.setText(original_text)
        self.txt_translated.setText(translated_text)
        
        # Reset lại trạng thái ngôi sao mỗi lần dịch câu mới
        self.btn_star.setProperty("class", "")
        self.style().unpolish(self.btn_star)
        self.style().polish(self.btn_star)

        # Tính toán vị trí popup để không bị che mất
        cursor_pos = QCursor.pos()
        offset_x, offset_y = 15, 15
        
        # Điều chỉnh nếu popup sẽ vượt ra ngoài màn hình
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
        # Lấy text hiện tại
        orig = self.txt_original.toPlainText().strip()
        trans = self.txt_translated.toPlainText().strip()
        
        # Validation: kiểm tra text không được rỗng
        if not orig or not trans:
            # Hiển thị feedback rằng không thể lưu text rỗng
            self.btn_star.setToolTip("Không thể lưu: Text không được để trống")
            # Nhấp nháy button để báo lỗi
            self.btn_star.setStyleSheet("color: #e74c3c;")  # Màu đỏ
            # Reset sau 1 giây
            QTimer.singleShot(1000, self._reset_star_button)
            return
        
        # Đổi trạng thái ngôi sao sang Vàng để báo hiệu đã bấm
        self.btn_star.setProperty("class", "saved")
        self.style().unpolish(self.btn_star)
        self.style().polish(self.btn_star)
        self.btn_star.setToolTip("Đã lưu vào sổ tay ✓")
        
        # Phát tín hiệu mang theo dữ liệu (main.py sẽ bắt tín hiệu này)
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