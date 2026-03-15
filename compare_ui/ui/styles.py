"""QSS styles for the subtitle compare tool."""

MAIN_STYLE = """
QMainWindow {
    background-color: #2b2b2b;
}

QWidget {
    font-family: "Microsoft YaHei", "SimHei", "Segoe UI", sans-serif;
    font-size: 12px;
}

/* Toolbar */
QToolBar {
    background-color: #3c3f41;
    border: none;
    padding: 4px;
    spacing: 4px;
}

QToolBar QToolButton {
    background-color: #4b6eaf;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 3px;
    font-weight: bold;
}

QToolBar QToolButton:hover {
    background-color: #5a7fc0;
}

QToolBar QToolButton:pressed {
    background-color: #3d5a8f;
}

QToolBar QToolButton:disabled {
    background-color: #555555;
    color: #888888;
}

/* Splitter */
QSplitter::handle {
    background-color: #555555;
}

QSplitter::handle:horizontal {
    width: 4px;
}

/* List Widget */
QListWidget {
    background-color: #2b2b2b;
    border: 1px solid #555555;
    color: #bbbbbb;
    outline: none;
}

QListWidget::item {
    background-color: #3c3f41;
    border-bottom: 1px solid #555555;
    padding: 8px;
    min-height: 60px;
}

QListWidget::item:selected {
    background-color: #4b6eaf;
    color: white;
}

QListWidget::item:hover {
    background-color: #4e5254;
}

/* Table Widget */
QTableWidget {
    background-color: #2b2b2b;
    border: 1px solid #555555;
    color: #bbbbbb;
    gridline-color: #555555;
    outline: none;
}

QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #555555;
}

QTableWidget::item:selected {
    background-color: #4b6eaf;
    color: white;
}

QHeaderView::section {
    background-color: #3c3f41;
    color: #bbbbbb;
    padding: 6px;
    border: none;
    border-right: 1px solid #555555;
    font-weight: bold;
}

/* Line Edit */
QLineEdit {
    background-color: #45494a;
    border: 1px solid #646464;
    color: #bbbbbb;
    padding: 4px;
    border-radius: 2px;
}

QLineEdit:focus {
    border-color: #4b6eaf;
}

/* Text Edit */
QTextEdit {
    background-color: #45494a;
    border: 1px solid #646464;
    color: #bbbbbb;
    padding: 4px;
    border-radius: 2px;
}

QTextEdit:focus {
    border-color: #4b6eaf;
}

/* Scroll Bar */
QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #595b5d;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6b6d6f;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #595b5d;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #6b6d6f;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #3c3f41;
    color: #bbbbbb;
}

QStatusBar::item {
    border: none;
}

/* Menu */
QMenu {
    background-color: #3c3f41;
    border: 1px solid #555555;
    color: #bbbbbb;
}

QMenu::item {
    padding: 6px 24px;
}

QMenu::item:selected {
    background-color: #4b6eaf;
    color: white;
}

QMenu::separator {
    height: 1px;
    background-color: #555555;
    margin: 4px 8px;
}

/* Dialog */
QDialog {
    background-color: #2b2b2b;
}

QLabel {
    color: #bbbbbb;
}

QPushButton {
    background-color: #4b6eaf;
    color: white;
    border: none;
    padding: 6px 16px;
    border-radius: 3px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #5a7fc0;
}

QPushButton:pressed {
    background-color: #3d5a8f;
}

QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}

/* Group Box */
QGroupBox {
    color: #bbbbbb;
    border: 1px solid #555555;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
"""

# Status colors for SRT entries
STATUS_COLORS = {
    'normal': '#3c3f41',      # Green - matched
    'offset': '#5a4a1f',      # Yellow - time offset
    'missing': '#5a2a2a',     # Red - missing
    'extra': '#3a3a3a',       # Gray - extra
}

STATUS_TEXT_COLORS = {
    'normal': '#90ee90',
    'offset': '#ffd700',
    'missing': '#ff6b6b',
    'extra': '#888888',
}
