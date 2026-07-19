"""VobSub panel for displaying subtitle images."""

import sys
import os

# Add parent directory to path for imports
_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QHBoxLayout, QPushButton, QDialog, QScrollArea,
    QMessageBox, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage, QStandardItemModel
from PIL import Image
import io

from core.models import VobSubEntry
from core.vobsub_parser import VobSubParser


class VobSubItemWidget(QWidget):
    """Custom widget for VobSub list item."""

    def __init__(self, entry: VobSubEntry, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(12)

        # Info (now on the left)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Index and time
        index_label = QLabel(f"#{self.entry.index}")
        index_label.setStyleSheet("font-weight: bold; color: #4b6eaf; font-size: 14px;")
        info_layout.addWidget(index_label)

        time_label = QLabel(f"{self.entry.start_time_str} --> {self.entry.end_time_str}")
        time_label.setStyleSheet("color: #bbbbbb; font-family: Consolas, monospace;")
        info_layout.addWidget(time_label)

        duration_label = QLabel(f"Duration: {self.entry.duration}ms")
        duration_label.setStyleSheet("color: #888888; font-size: 10px;")
        info_layout.addWidget(duration_label)

        layout.addLayout(info_layout)

        # Spacer to push thumbnail to the right
        layout.addStretch(stretch=1)

        # Thumbnail (now on the right)
        self.thumb_label = QLabel()
        # Set fixed size to accommodate subtitle images
        # VobSub subtitle images vary in height (single line ~40px, double line ~80px)
        self.thumb_label.setFixedSize(400, 140)
        self.thumb_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #555; color: #666;")
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setText("Loading...")
        layout.addWidget(self.thumb_label)

    def set_thumbnail(self, pixmap: QPixmap):
        """Set the thumbnail image."""
        if not pixmap.isNull():
            # Scale to fit within 396x136 while keeping full image visible
            scaled = pixmap.scaled(
                396,
                136,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.thumb_label.setPixmap(scaled)


class ImageViewerDialog(QDialog):
    """Dialog for viewing full-size subtitle image."""

    def __init__(self, pixmap: QPixmap, entry: VobSubEntry, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Subtitle #{entry.index} - {entry.start_time_str}")
        self.setMinimumSize(800, 600)
        self.setup_ui(pixmap, entry)

    def setup_ui(self, pixmap: QPixmap, entry: VobSubEntry):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for image
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1a1a1a;")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setPixmap(pixmap)

        scroll.setWidget(self.image_label)
        layout.addWidget(scroll)

        # Info bar
        info_bar = QWidget()
        info_bar.setStyleSheet("background-color: #3c3f41; padding: 8px;")
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(12, 8, 12, 8)

        info_text = f"#{entry.index} | {entry.start_time_str} --> {entry.end_time_str} | Duration: {entry.duration}ms"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #bbbbbb; font-family: Consolas, monospace;")
        info_layout.addWidget(info_label)

        info_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        info_layout.addWidget(close_btn)

        layout.addWidget(info_bar)


class VobSubPanel(QWidget):
    """Panel for displaying VobSub subtitle images."""

    entry_selected = pyqtSignal(int)  # Emit index when entry selected
    file_dropped = pyqtSignal(str)  # Emit file path when file is dropped

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parser: VobSubParser = None
        self.entries: list[VobSubEntry] = []
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

        title = QLabel("VobSub (Image)")
        title.setStyleSheet("font-weight: bold; color: #bbbbbb; font-size: 14px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.count_label = QLabel("No file loaded")
        self.count_label.setStyleSheet("color: #888888;")
        header_layout.addWidget(self.count_label)

        layout.addWidget(header)

        # Column header matching the SRT table header implementation and style
        self.column_header = QHeaderView(Qt.Orientation.Horizontal)
        self.column_header_model = QStandardItemModel(0, 2, self.column_header)
        self.column_header_model.setHorizontalHeaderLabels(["Info", "Image"])
        self.column_header.setModel(self.column_header_model)
        self.column_header.setSectionsClickable(False)
        self.column_header.setHighlightSections(False)
        self.column_header.setSectionsMovable(False)
        self.column_header.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.column_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.column_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.column_header.resizeSection(1, 416)
        layout.addWidget(self.column_header)

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(2)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)

        # Drop area overlay (shown when empty)
        self.drop_label = QLabel("Drop IDX file here\nor click Import VobSub")
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
                if file_path.lower().endswith('.idx'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self.drop_label.hide()
        self.list_widget.show()

    def dropEvent(self, event):
        """Handle drop event."""
        self.drop_label.hide()
        self.list_widget.show()

        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            if file_path.lower().endswith('.idx'):
                self.file_dropped.emit(file_path)
                event.acceptProposedAction()
                return
        event.ignore()

    def show_drop_area(self):
        """Show drop area when empty."""
        if not self.entries:
            self.list_widget.hide()
            self.drop_label.show()

    def hide_drop_area(self):
        """Hide drop area."""
        self.drop_label.hide()
        self.list_widget.show()

    def load_vobsub(self, idx_path: str, fps: str = 'ntsc') -> bool:
        """Load VobSub file.

        Args:
            idx_path: Path to IDX file
            fps: Frame rate ('23.976', '24', '25', '29.97', '30', 'keep')
        """
        try:
            self.parser = VobSubParser(fps=fps)
            self.entries = self.parser.parse(idx_path)
            self.hide_drop_area()
            self.populate_list()
            self.count_label.setText(f"{len(self.entries)} entries")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load VobSub:\n{str(e)}")
            return False

    def populate_list(self):
        """Populate the list with VobSub entries."""
        self.list_widget.clear()

        for entry in self.entries:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, entry.index)
            item.setSizeHint(QSize(420, 140))

            widget = VobSubItemWidget(entry)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

            # Load thumbnail asynchronously
            self.load_thumbnail(widget, entry)

    def load_thumbnail(self, widget: VobSubItemWidget, entry: VobSubEntry):
        """Load thumbnail image for entry."""
        try:
            if self.parser:
                img = self.parser.get_image(entry)
                if img:
                    # Convert PIL Image to QPixmap
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    data = img.tobytes('raw', 'RGBA')
                    qimage = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
                    pixmap = QPixmap.fromImage(qimage)
                    widget.set_thumbnail(pixmap)
        except Exception as e:
            print(f"Error loading thumbnail for entry {entry.index}: {e}")

    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click."""
        index = item.data(Qt.ItemDataRole.UserRole)
        self.entry_selected.emit(index)

    def on_item_double_clicked(self, item: QListWidgetItem):
        """Handle item double click - show full image."""
        index = item.data(Qt.ItemDataRole.UserRole)
        entry = next((e for e in self.entries if e.index == index), None)
        if entry and self.parser:
            try:
                img = self.parser.get_image(entry)
                if img:
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    data = img.tobytes('raw', 'RGBA')
                    qimage = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
                    pixmap = QPixmap.fromImage(qimage)

                    dialog = ImageViewerDialog(pixmap, entry, self)
                    dialog.exec()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load image: {str(e)}")

    def select_entry(self, index: int):
        """Select entry by index."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == index:
                self.list_widget.setCurrentItem(item)
                # Scroll to make item visible at top
                self.list_widget.scrollToItem(item, QListWidget.ScrollHint.PositionAtTop)
                break

    def scroll_to_row(self, row: int):
        """Scroll to specific row by index (0-based)."""
        if 0 <= row < self.list_widget.count():
            item = self.list_widget.item(row)
            if item:
                self.list_widget.scrollToItem(item, QListWidget.ScrollHint.PositionAtTop)

    def get_row_scroll_position(self, row: int) -> int:
        """Get the scroll position needed to show a specific row at the top."""
        if 0 <= row < self.list_widget.count():
            # Calculate position: row index * row height + spacing
            return row * 140  # 140 is the fixed row height
        return 0

    def scroll_to_row_at_top(self, row: int):
        """Scroll to make a specific row appear at the top of the viewport."""
        if 0 <= row < self.list_widget.count():
            target_pos = self.get_row_scroll_position(row)
            scrollbar = self.list_widget.verticalScrollBar()
            scrollbar.setValue(min(target_pos, scrollbar.maximum()))

    def get_row_viewport_y(self, row: int) -> int | None:
        """Return the row's top Y coordinate relative to the list viewport."""
        if not 0 <= row < self.list_widget.count():
            return None
        item = self.list_widget.item(row)
        return self.list_widget.visualItemRect(item).top()

    def align_row_to_viewport_y(self, row: int, target_y: int):
        """Scroll until a row is as close as possible to target_y."""
        current_y = self.get_row_viewport_y(row)
        if current_y is None:
            return
        scrollbar = self.list_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() + current_y - target_y)

    def clear(self):
        """Clear all entries."""
        self.list_widget.clear()
        self.entries = []
        self.parser = None
        self.count_label.setText("No file loaded")
        self.show_drop_area()
