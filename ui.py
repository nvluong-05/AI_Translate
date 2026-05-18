from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QApplication, 
                             QPushButton, QSystemTrayIcon, QMenu, QListWidget, QListWidgetItem, QDialog,
                             QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor, QFont, QIcon
import json
import os

class HistoryWindow(QDialog):
    """Cửa sổ quản lý từ vựng và lịch sử"""
    delete_vocab_signal = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vocab_list = []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Sổ Tay Từ Vựng")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { color: #333333; font-weight: bold; }
            QListWidget { border: 1px solid #ddd; background-color: #f9f9f9; }
            QListWidgetItem { padding: 5px; }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton#deleteBtn {
                background-color: #e74c3c;
            }
            QPushButton#deleteBtn:hover { background-color: #c0392b; }
        """)
        
        layout = QVBoxLayout()
        
        title = QLabel("📚 Sổ Tay Từ Vựng - Quản Lý Từ Đã Lưu")
        layout.addWidget(title)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        button_layout = QHBoxLayout()
        
        self.btn_delete_all = QPushButton("🗑️ Xóa Tất Cả")
        self.btn_delete_all.setObjectName("deleteBtn")
        self.btn_delete_all.clicked.connect(self.delete_all_vocab)
        
        self.btn_refresh = QPushButton("🔄 Làm Mới")
        self.btn_refresh.clicked.connect(self.refresh_list)
        
        self.btn_close = QPushButton("❌ Đóng")
        self.btn_close.clicked.connect(self.close)
        
        button_layout.addWidget(self.btn_delete_all)
        button_layout.addWidget(self.btn_refresh)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_close)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def set_vocab_list(self, vocab_list):
        """Cập nhật danh sách từ vựng"""
        self.vocab_list = vocab_list
        self.refresh_list()
    
    def refresh_list(self):
        """Làm mới danh sách hiển thị"""
        self.list_widget.clear()
        for idx, item in enumerate(self.vocab_list):
            if isinstance(item, dict):
                original = item.get("original", "")
                translation = item.get("translation", "")
            else:
                original, translation = item
            
            display_text = f"{original} → {translation}"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.ItemDataRole.UserRole, idx)
            self.list_widget.addItem(list_item)
            
            # Thêm nút xóa cho mỗi item
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.addWidget(QLabel(display_text))
            delete_btn = QPushButton("✕")
            delete_btn.setMaximumWidth(30)
            delete_btn.setObjectName("deleteBtn")
            delete_btn.clicked.connect(lambda checked, i=idx: self.delete_vocab(i))
            item_layout.addStretch()
            item_layout.addWidget(delete_btn)
            item_widget.setLayout(item_layout)
    
    def delete_vocab(self, index):
        """Xóa một từ vựng"""
        if 0 <= index < len(self.vocab_list):
            self.vocab_list.pop(index)
            self.delete_vocab_signal.emit(index)
            self.refresh_list()
    
    def delete_all_vocab(self):
        """Xóa tất cả từ vựng"""
        reply = QMessageBox.question(
            self, 
            "Xác Nhận", 
            "Bạn có chắc chắn muốn xóa tất cả từ vựng không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.vocab_list.clear()
            self.list_widget.clear()
            self.delete_vocab_signal.emit(-1)  # -1 để xóa tất cả

class TranslationPopup(QWidget):
    save_vocab_signal = pyqtSignal(str, str)
    show_history_signal = pyqtSignal()
    close_app_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.history_window = None
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
            /* Style riêng cho các nút */
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 18px;
                color: #7f8c8d;
                cursor: pointer;
            }
            QPushButton:hover { color: #2c3e50; }
            QPushButton#starButton {
                font-size: 20px;
                color: #bdc3c7;
            }
            QPushButton#starButton:hover { color: #f1c40f; }
            QPushButton#starButton.saved { color: #f1c40f; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)

        # Header với các nút điều khiển
        header_layout = QHBoxLayout()
        self.lbl_translated = QLabel("Bản dịch:")
        
        self.btn_star = QPushButton("⭐")
        self.btn_star.setObjectName("starButton")
        self.btn_star.setToolTip("Lưu vào sổ tay")
        self.btn_star.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_star.clicked.connect(self.on_star_clicked)
        self.btn_star.setMaximumWidth(40)

        self.btn_history = QPushButton("📚")
        self.btn_history.setToolTip("Xem sổ tay từ vựng")
        self.btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_history.clicked.connect(self.show_history)
        self.btn_history.setMaximumWidth(40)

        self.btn_minimize = QPushButton("▼")
        self.btn_minimize.setToolTip("Thu nhỏ")
        self.btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_minimize.clicked.connect(self.hide)
        self.btn_minimize.setMaximumWidth(40)

        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Tắt ứng dụng")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.request_close_app)
        self.btn_close.setMaximumWidth(40)

        header_layout.addWidget(self.lbl_translated)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_star)
        header_layout.addWidget(self.btn_history)
        header_layout.addWidget(self.btn_minimize)
        header_layout.addWidget(self.btn_close)

        self.txt_translated = QTextEdit()
        self.txt_translated.setReadOnly(True)
        self.txt_translated.setFont(QFont("Arial", 11))

        self.lbl_original = QLabel("Bản gốc:")
        self.txt_original = QTextEdit()
        self.txt_original.setReadOnly(True)
        self.txt_original.setFont(QFont("Arial", 10))
        self.txt_original.setMaximumHeight(60)

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

    def show_history(self):
        """Mở cửa sổ quản lý từ vựng"""
        if self.history_window is None:
            self.history_window = HistoryWindow(self)
            self.history_window.delete_vocab_signal.connect(self.on_vocab_deleted)
        
        self.show_history_signal.emit()
        self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()

    def set_history_data(self, vocab_list):
        """Cập nhật dữ liệu lịch sử cho cửa sổ"""
        if self.history_window:
            self.history_window.set_vocab_list(vocab_list)

    def on_vocab_deleted(self, index):
        """Xử lý khi xóa từ vựng từ cửa sổ lịch sử"""
        pass

    def request_close_app(self):
        """Gửi tín hiệu yêu cầu tắt ứng dụng"""
        reply = QMessageBox.question(
            self,
            "Xác Nhận",
            "Bạn có chắc chắn muốn tắt ứng dụng?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close_app_signal.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()


class TrayIconApp:
    """Quản lý System Tray Icon"""
    show_popup_signal = pyqtSignal()
    
    def __init__(self, popup_window):
        self.popup_window = popup_window
        self.tray_icon = QSystemTrayIcon()
        self.setup_tray_menu()
    
    def setup_tray_menu(self):
        """Thiết lập menu cho system tray"""
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("🔍 Hiện cửa sổ")
        show_action.triggered.connect(self.show_popup)
        
        history_action = tray_menu.addAction("📚 Xem sổ tay")
        history_action.triggered.connect(self.open_history)
        
        tray_menu.addSeparator()
        
        exit_action = tray_menu.addAction("❌ Thoát")
        exit_action.triggered.connect(self.exit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
    
    def show_popup(self):
        """Hiển thị cửa sổ popup"""
        self.popup_window.show()
        self.popup_window.raise_()
        self.popup_window.activateWindow()
    
    def open_history(self):
        """Mở cửa sổ sổ tay"""
        self.popup_window.show_history()
    
    def exit_app(self):
        """Thoát ứng dụng"""
        reply = QMessageBox.question(
            self.popup_window,
            "Xác Nhận",
            "Bạn có chắc chắn muốn thoát ứng dụng?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()
    
    def show_icon(self):
        """Hiển thị icon trong system tray"""
        self.tray_icon.show()
    
    def hide_icon(self):
        """Ẩn icon trong system tray"""
        self.tray_icon.hide()
