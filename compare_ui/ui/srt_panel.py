"""SRT panel for editing subtitle text."""

import sys
import os

# Add parent directory to path for imports
_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QTextEdit,
    QHeaderView, QMenu, QAbstractItemView, QMessageBox,
    QDialog, QFormLayout, QTimeEdit, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTime
from PyQt6.QtGui import QAction, QColor

from core.models import SRTEntry
from core.srt_parser import SRTParser
from ui.styles import STATUS_COLORS, STATUS_TEXT_COLORS


class TimeEditDialog(QDialog):
    """Dialog for editing subtitle time."""

    def __init__(self, start_ms: int, end_ms: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Time")
        self.setMinimumWidth(300)
        self.setup_ui(start_ms, end_ms)

    def setup_ui(self, start_ms: int, end_ms: int):
        layout = QFormLayout(self)

        # Start time
        self.start_edit = QTimeEdit()
        self.start_edit.setDisplayFormat("HH:mm:ss,zzz")
        self.start_edit.setTime(self.ms_to_qtime(start_ms))
        layout.addRow("Start Time:", self.start_edit)

        # End time
        self.end_edit = QTimeEdit()
        self.end_edit.setDisplayFormat("HH:mm:ss,zzz")
        self.end_edit.setTime(self.ms_to_qtime(end_ms))
        layout.addRow("End Time:", self.end_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def ms_to_qtime(self, ms: int) -> QTime:
        """Convert milliseconds to QTime."""
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        milliseconds = ms % 1000
        return QTime(hours, minutes, seconds, milliseconds)

    def get_times(self) -> tuple[int, int]:
        """Get start and end times in milliseconds."""
        start = self.start_edit.time()
        end = self.end_edit.time()
        start_ms = (start.hour() * 3600000 + start.minute() * 60000 +
                   start.second() * 1000 + start.msec())
        end_ms = (end.hour() * 3600000 + end.minute() * 60000 +
                 end.second() * 1000 + end.msec())
        return start_ms, end_ms


class SRTPanel(QWidget):
    """Panel for editing SRT subtitles."""

    entry_selected = pyqtSignal(int)  # Emit index when entry selected
    data_changed = pyqtSignal()  # Emit when data changes
    file_dropped = pyqtSignal(str)  # Emit file path when file is dropped

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parser: SRTParser = None
        self.entries: list[SRTEntry] = []
        self.match_status: dict[int, str] = {}  # index -> status
        self.setup_ui()
        self.setup_drag_drop()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #3c3f41; padding: 8px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel("SRT (Text)")
        title.setStyleSheet("font-weight: bold; color: #bbbbbb; font-size: 14px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(8)

        for status, color in [
            ('normal', '#90ee90'),
            ('offset', '#ffd700'),
            ('missing', '#ff6b6b'),
            ('extra', '#888888')
        ]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 10px;")
            legend_layout.addWidget(dot)
            label = QLabel(status.capitalize())
            label.setStyleSheet(f"color: {color}; font-size: 10px;")
            legend_layout.addWidget(label)

        header_layout.addLayout(legend_layout)
        header_layout.addSpacing(20)

        self.count_label = QLabel("No file loaded")
        self.count_label.setStyleSheet("color: #888888;")
        header_layout.addWidget(self.count_label)

        layout.addWidget(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['#', 'Start', 'End', 'Text'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        # Set default row height to match VobSub panel (140 pixels)
        self.table.verticalHeader().setDefaultSectionSize(140)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        self.table.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.table)

        # Drop area overlay (shown when empty)
        self.drop_label = QLabel("Drop SRT file here\nor click Import SRT")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 16px;
                border: 2px dashed #555555;
                border-radius: 8px;
                background-color: #2b2b2b;
                padding: 40px;
            }
        """)
        self.drop_label.hide()
        layout.addWidget(self.drop_label)

    def setup_drag_drop(self):
        """Setup drag and drop functionality."""
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.srt'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self.drop_label.hide()
        self.table.show()

    def dropEvent(self, event):
        """Handle drop event."""
        self.drop_label.hide()
        self.table.show()

        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            if file_path.lower().endswith('.srt'):
                self.file_dropped.emit(file_path)
                event.acceptProposedAction()
                return
        event.ignore()

    def show_drop_area(self):
        """Show drop area when empty."""
        if not self.entries:
            self.table.hide()
            self.drop_label.show()

    def hide_drop_area(self):
        """Hide drop area."""
        self.drop_label.hide()
        self.table.show()

    def load_srt(self, file_path: str) -> bool:
        """Load SRT file."""
        try:
            self.parser = SRTParser()
            self.hide_drop_area()
            self.entries = self.parser.parse(file_path)
            self.populate_table()
            self.count_label.setText(f"{len(self.entries)} entries")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load SRT:\n{str(e)}")
            return False

    def load_entries(self, entries: list):
        """Load SRT entries directly (e.g., from OCR)."""
        self.hide_drop_area()
        self.entries = entries
        # Create parser for saving when loading from OCR
        self.parser = SRTParser()
        self.parser.entries = entries
        self.populate_table()
        self.count_label.setText(f"{len(self.entries)} entries")

    def populate_table(self):
        """Populate table with entries."""
        self.table.setRowCount(len(self.entries))
        self.table.blockSignals(True)

        for row, entry in enumerate(self.entries):
            # Index
            index_item = QTableWidgetItem(str(entry.index))
            index_item.setFlags(index_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            index_item.setData(Qt.ItemDataRole.UserRole, entry.index)
            self.table.setItem(row, 0, index_item)

            # Start time
            start_item = QTableWidgetItem(entry.start_time_str)
            self.table.setItem(row, 1, start_item)

            # End time
            end_item = QTableWidgetItem(entry.end_time_str)
            self.table.setItem(row, 2, end_item)

            # Text
            text_item = QTableWidgetItem(entry.text.replace('\n', ' '))
            self.table.setItem(row, 3, text_item)

            # Apply status color
            self.update_row_color(row, 'normal')

        self.table.blockSignals(False)

    def update_row_color(self, row: int, status: str):
        """Update row background color based on match status."""
        color = STATUS_COLORS.get(status, STATUS_COLORS['normal'])
        text_color = STATUS_TEXT_COLORS.get(status, STATUS_TEXT_COLORS['normal'])

        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(Qt.GlobalColor.transparent)
                item.setData(Qt.ItemDataRole.BackgroundRole, None)
                # Store status for later use
                item.setData(Qt.ItemDataRole.UserRole + 1, status)

        # Apply stylesheet to row via delegate would be better, but we'll use item background
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                from PyQt6.QtGui import QColor
                item.setBackground(QColor(color))
                item.setForeground(QColor(text_color))

    def set_match_status(self, index: int, status: str):
        """Set match status for an entry."""
        self.match_status[index] = status
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == index:
                self.update_row_color(row, status)
                break

    def on_cell_clicked(self, row: int, column: int):
        """Handle cell click."""
        item = self.table.item(row, 0)
        if item:
            index = item.data(Qt.ItemDataRole.UserRole)
            self.entry_selected.emit(index)

    def on_cell_double_clicked(self, row: int, column: int):
        """Handle cell double click - edit time."""
        if column in (1, 2):  # Start or End time
            item = self.table.item(row, 0)
            if item and self.parser:
                index = item.data(Qt.ItemDataRole.UserRole)
                entry = self.parser.get_entry(index)
                if entry:
                    dialog = TimeEditDialog(entry.start_time, entry.end_time, self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        start_ms, end_ms = dialog.get_times()
                        entry.start_time = start_ms
                        entry.end_time = end_ms
                        self.table.item(row, 1).setText(entry.start_time_str)
                        self.table.item(row, 2).setText(entry.end_time_str)
                        self.data_changed.emit()

    def on_item_changed(self, item: QTableWidgetItem):
        """Handle item edit."""
        row = item.row()
        col = item.column()

        if row < 0 or row >= len(self.entries):
            return

        entry = self.entries[row]

        if col == 1:  # Start time
            try:
                entry.start_time = SRTEntry.parse_time(item.text())
                self.data_changed.emit()
            except ValueError:
                item.setText(entry.start_time_str)
        elif col == 2:  # End time
            try:
                entry.end_time = SRTEntry.parse_time(item.text())
                self.data_changed.emit()
            except ValueError:
                item.setText(entry.end_time_str)
        elif col == 3:  # Text
            entry.text = item.text()
            self.data_changed.emit()

    def show_context_menu(self, position):
        """Show context menu."""
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        self.table.selectRow(row)

        menu = QMenu(self)

        add_action = QAction("Add Entry", self)
        add_action.triggered.connect(lambda: self.add_entry(row))
        menu.addAction(add_action)

        duplicate_action = QAction("Duplicate Entry", self)
        duplicate_action.triggered.connect(lambda: self.duplicate_entry(row))
        menu.addAction(duplicate_action)

        delete_action = QAction("Delete Entry", self)
        delete_action.triggered.connect(lambda: self.delete_entry(row))
        menu.addAction(delete_action)

        menu.addSeparator()

        edit_time_action = QAction("Edit Time...", self)
        edit_time_action.triggered.connect(lambda: self.edit_time(row))
        menu.addAction(edit_time_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def add_entry(self, after_row: int):
        """Add new entry after specified row."""
        if not self.parser or after_row >= len(self.entries):
            return

        ref_entry = self.entries[after_row]
        new_entry = SRTEntry(
            index=after_row + 2,
            start_time=ref_entry.end_time + 100,
            end_time=ref_entry.end_time + 2100,
            text="New subtitle",
            editable=True
        )

        self.entries.insert(after_row + 1, new_entry)
        self.parser._reindex()
        self.populate_table()
        self.data_changed.emit()

    def duplicate_entry(self, row: int):
        """Duplicate entry at specified row."""
        if not self.parser or row >= len(self.entries):
            return

        entry = self.entries[row]
        new_entry = SRTEntry(
            index=entry.index + 1,
            start_time=entry.start_time,
            end_time=entry.end_time,
            text=entry.text,
            editable=True
        )

        self.entries.insert(row + 1, new_entry)
        self.parser._reindex()
        self.populate_table()
        self.data_changed.emit()

    def delete_entry(self, row: int):
        """Delete entry at specified row."""
        if not self.parser or row >= len(self.entries):
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete entry #{self.entries[row].index}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.entries[row]
            self.parser._reindex()
            self.populate_table()
            self.data_changed.emit()

    def edit_time(self, row: int):
        """Open time edit dialog."""
        self.on_cell_double_clicked(row, 1)

    def select_entry(self, index: int):
        """Select entry by index."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == index:
                self.table.selectRow(row)
                # Scroll to make row visible at top
                self.table.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtTop)
                break

    def scroll_to_row(self, row: int):
        """Scroll to specific row by index (0-based)."""
        if 0 <= row < self.table.rowCount():
            item = self.table.item(row, 0)
            if item:
                self.table.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtTop)

    def get_row_scroll_position(self, row: int) -> int:
        """Get the scroll position needed to show a specific row at the top."""
        if 0 <= row < self.table.rowCount():
            # Calculate position: row index * row height
            return row * 140  # 140 is the fixed row height
        return 0

    def scroll_to_row_at_top(self, row: int):
        """Scroll to make a specific row appear at the top of the viewport."""
        if 0 <= row < self.table.rowCount():
            target_pos = self.get_row_scroll_position(row)
            scrollbar = self.table.verticalScrollBar()
            scrollbar.setValue(min(target_pos, scrollbar.maximum()))

    def get_row_viewport_y(self, row: int) -> int | None:
        """Return the row's top Y coordinate relative to the table viewport."""
        if not 0 <= row < self.table.rowCount():
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        return self.table.visualItemRect(item).top()

    def align_row_to_viewport_y(self, row: int, target_y: int):
        """Scroll until a row is as close as possible to target_y."""
        current_y = self.get_row_viewport_y(row)
        if current_y is None:
            return
        scrollbar = self.table.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() + current_y - target_y)

    def save(self, file_path: str = None) -> bool:
        """Save SRT file."""
        if self.parser:
            return self.parser.save(file_path)
        return False

    def clear(self):
        """Clear all entries."""
        self.table.setRowCount(0)
        self.entries = []
        self.parser = None
        self.match_status = {}
        self.count_label.setText("No file loaded")
        self.show_drop_area()

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        # Simplified - in real app, track modifications
        return len(self.entries) > 0
