import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QComboBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

import utils


def fetch_vocab(search="", tag="Tất cả"):
    utils.init_db()
    conn = sqlite3.connect(utils.DB_PATH)
    cursor = conn.cursor()
    query = "SELECT id, word, definition, phonetics, tag, timestamp FROM data WHERE 1=1"
    params = []
    if search:
        query += " AND (word LIKE ? OR definition LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if tag and tag != "Tất cả":
        query += " AND tag = ?"
        params.append(tag)
    query += " ORDER BY timestamp DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_tags():
    utils.init_db()
    conn = sqlite3.connect(utils.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT tag FROM data WHERE tag IS NOT NULL ORDER BY tag")
    tags = [r[0] for r in cursor.fetchall()]
    conn.close()
    return tags


def delete_vocab(word_id: int):
    conn = sqlite3.connect(utils.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM data WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()


class HistoryWindow(QWidget):
    def __init__(self, popup=None):
        super().__init__()
        self.popup = popup
        self.setWindowTitle("📚 Sổ tay từ vựng")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("""
            QWidget { background-color: #f5f6fa; font-family: Arial; }
            QLabel#title { font-size: 18px; font-weight: bold; color: #2c3e50; border: none; }
            QLabel#count { font-size: 12px; color: #7f8c8d; border: none; }
            QLineEdit {
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 6px 10px;
                background: white;
                font-size: 13px;
            }
            QComboBox {
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 5px 10px;
                background: white;
                font-size: 13px;
            }
            QTableWidget {
                background: white;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                gridline-color: #f0f0f0;
                font-size: 13px;
            }
            QTableWidget::item { padding: 8px; border: none; }
            QTableWidget::item:selected { background-color: #dfe6e9; color: #2c3e50; }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #555;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #dcdde1;
            }
            QPushButton#deleteBtn {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 12px;
            }
            QPushButton#deleteBtn:hover { background-color: #c0392b; }
            QPushButton#refreshBtn {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton#refreshBtn:hover { background-color: #2980b9; }
        """)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title_row = QHBoxLayout()
        lbl_title = QLabel("📚 Sổ tay từ vựng")
        lbl_title.setObjectName("title")
        self.lbl_count = QLabel("0 từ")
        self.lbl_count.setObjectName("count")
        title_row.addWidget(lbl_title)
        title_row.addStretch()
        title_row.addWidget(self.lbl_count)

        filter_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Tìm kiếm từ hoặc nghĩa...")
        self.search_box.textChanged.connect(self._on_search)

        self.tag_filter = QComboBox()
        self.tag_filter.setFixedWidth(130)
        self.tag_filter.currentTextChanged.connect(self._on_search)

        btn_refresh = QPushButton("🔄 Làm mới")
        btn_refresh.setObjectName("refreshBtn")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self.load_data)

        filter_row.addWidget(self.search_box)
        filter_row.addWidget(self.tag_filter)
        filter_row.addWidget(btn_refresh)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["#", "Từ / Cụm từ", "Nghĩa", "Phiên âm", "Tag", "Xoá"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed);      self.table.setColumnWidth(0, 40)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive); self.table.setColumnWidth(1, 150)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive); self.table.setColumnWidth(3, 110)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed);      self.table.setColumnWidth(4, 80)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed);      self.table.setColumnWidth(5, 60)

        layout.addLayout(title_row)
        layout.addLayout(filter_row)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_data(self):
        current_tag = self.tag_filter.currentText()
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("Tất cả")
        self.tag_filter.addItems(fetch_tags())
        idx = self.tag_filter.findText(current_tag)
        self.tag_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.tag_filter.blockSignals(False)

        self._render_table()

    def _on_search(self):
        self._render_table()

    def _render_table(self):
        search = self.search_box.text().strip()
        tag    = self.tag_filter.currentText()
        rows   = fetch_vocab(search, tag)

        self.table.setRowCount(len(rows))
        self.lbl_count.setText(f"{len(rows)} từ")

        for i, (row_id, word, definition, phonetics, tag_val, timestamp) in enumerate(rows):
            display_def = definition
            if "Dịch:" in definition:
                for part in definition.split("|"):
                    if "Dịch:" in part:
                        display_def = part.replace("Dịch:", "").strip()
                        break

            self.table.setItem(i, 0, self._cell(str(i + 1), center=True))
            self.table.setItem(i, 1, self._cell(word))
            self.table.setItem(i, 2, self._cell(display_def))
            self.table.setItem(i, 3, self._cell(phonetics or ""))
            self.table.setItem(i, 4, self._cell(tag_val or "", center=True))

            btn_del = QPushButton("🗑")
            btn_del.setObjectName("deleteBtn")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setToolTip("Xoá từ này")
            btn_del.clicked.connect(lambda _, rid=row_id, w=word: self._confirm_delete(rid, w))
            self.table.setCellWidget(i, 5, btn_del)

            self.table.setRowHeight(i, 40)

    def _cell(self, text: str, center=False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    def _confirm_delete(self, row_id: int, word: str):
        msg = QMessageBox(self)
        msg.setWindowTitle("Xác nhận xoá")
        msg.setText(f"Xoá từ <b>'{word}'</b> khỏi sổ tay?")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if msg.exec() == QMessageBox.StandardButton.Yes:
            delete_vocab(row_id)
            self._render_table()

    def closeEvent(self, event):
        if self.popup:
            self.popup.show()
            self.popup.activateWindow()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()