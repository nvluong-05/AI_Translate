import sys
import time
import threading
import keyboard
import pyperclip
import pyautogui

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter

import utils
from ui import TranslationPopup
from translation import Translator
from history import HistoryWindow


def create_tray_icon():
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#3498db"))
    painter.setPen(QColor("white"))
    painter.drawEllipse(2, 2, 28, 28)
    painter.drawText(pixmap.rect(), 0x84, "T")
    painter.end()
    return QIcon(pixmap)


class HotkeyBridge(QObject):
    translate_triggered = pyqtSignal(str, int, int)

    def start_listening(self):
        t = threading.Thread(target=self._listen, daemon=True)
        t.start()

    def _listen(self):
        keyboard.add_hotkey('ctrl+q', self._on_hotkey)
        keyboard.wait()

    def _on_hotkey(self):
        x, y = pyautogui.position()
        pyperclip.copy("")
        keyboard.press_and_release('ctrl+c')  # copy text bôi đen
        time.sleep(0.5)
        text = pyperclip.paste().strip()
        if not text:
            return
        self.translate_triggered.emit(text, x, y)


class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        utils.init_db()

        self.translator = Translator()
        self.popup = TranslationPopup()
        self.popup.save_vocab_signal.connect(self.on_save_vocab)
        self.history_window = HistoryWindow(popup=self.popup)

        self.popup.btn_history.clicked.connect(self.open_history)
        self.popup.closeEvent = self.on_popup_close

        self.bridge = HotkeyBridge()
        self.bridge.translate_triggered.connect(
            self.on_translate_triggered,
            Qt.ConnectionType.QueuedConnection
        )
        self.bridge.start_listening()

        self._setup_tray()
        print("✅ AI Translate đang chạy ngầm!")
        print("📋 Bôi đen text → Ctrl+Q để dịch | Chuột phải icon khay để tắt")

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(create_tray_icon(), self.app)
        self.tray.setToolTip("AI Translate đang sẵn sàng")

        menu = QMenu()
        action_status = menu.addAction("🟢 Ứng dụng đang hoạt động")
        action_status.setEnabled(False)
        menu.addSeparator()
        action_show = menu.addAction("📖 Mở popup dịch")
        action_show.triggered.connect(self.popup.show)
        action_history = menu.addAction("📚 Sổ tay từ vựng")
        action_history.triggered.connect(self.open_history)
        menu.addSeparator()
        action_quit = menu.addAction("❌ Thoát ứng dụng")
        action_quit.triggered.connect(self.quit_app)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.popup.show()
            self.popup.activateWindow()

    def on_popup_close(self, event):
        msg = QMessageBox()
        msg.setWindowTitle("AI Translate")
        msg.setText("Bạn muốn đóng cửa sổ này?")
        msg.setIcon(QMessageBox.Icon.Question)
        btn_minimize = msg.addButton("Thu nhỏ xuống khay", QMessageBox.ButtonRole.AcceptRole)
        btn_quit     = msg.addButton("Tắt hẳn ứng dụng",  QMessageBox.ButtonRole.DestructiveRole)
        msg.addButton("Huỷ",                              QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == btn_minimize:
            event.ignore()
            self.popup.hide()
            self.tray.showMessage(
                "AI Translate",
                "App vẫn chạy ngầm. Ctrl+Q để dịch nhanh!",
                QSystemTrayIcon.MessageIcon.Information, 2000
            )
        elif clicked == btn_quit:
            self.quit_app()
        else:
            event.ignore()

    def open_history(self):
        self.history_window.load_data()
        self.popup.hide()
        self.history_window.show()
        self.history_window.activateWindow()

    def quit_app(self):
        self.tray.hide()
        QApplication.quit()

    def on_translate_triggered(self, original: str, x: int, y: int):
        result = self.translator.translate_text(original)
        if result:
            self.popup.show_translation_at(original, result, x, y)

    def on_save_vocab(self, original: str, translated: str):
        phonetics = ""
        if "Phiên âm:" in translated:
            for part in translated.split("|"):
                if "Phiên âm:" in part:
                    phonetics = part.replace("Phiên âm:", "").strip()
                    break
        success = utils.add_to_notebook(
            word=original,
            definition=translated,
            phonetics=phonetics,
            tag="General"
        )
        if success:
            self.tray.showMessage("AI Translate", f"✅ Đã lưu: '{original}'",
                                  QSystemTrayIcon.MessageIcon.Information, 2000)
            if self.history_window.isVisible():
                self.history_window.load_data()

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    controller = AppController()
    controller.run()