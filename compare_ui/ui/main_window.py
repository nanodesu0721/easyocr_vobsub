"""Main window for the subtitle compare tool."""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QPushButton, QFileDialog, QLabel, QMessageBox,
    QStatusBar, QProgressDialog, QApplication
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QKeySequence, QFont

from ui.vobsub_panel import VobSubPanel
from ui.srt_panel import SRTPanel
from ui.styles import MAIN_STYLE


class MainWindow(QMainWindow):
    """Main window for subtitle comparison tool."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SubtitleCompare - VobSub/SRT Comparison Tool")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self.settings = QSettings('SubtitleCompare', 'Main')
        self.vobsub_path = None
        self.srt_path = None
        self.modified = False

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup the user interface."""
        # Apply stylesheet
        self.setStyleSheet(MAIN_STYLE)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self.setup_toolbar()

        # Splitter with panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # VobSub panel (left)
        self.vobsub_panel = VobSubPanel()
        self.vobsub_panel.entry_selected.connect(self.on_vobsub_selected)
        self.vobsub_panel.file_dropped.connect(self.import_vobsub_from_drop)
        self.splitter.addWidget(self.vobsub_panel)

        # SRT panel (right)
        self.srt_panel = SRTPanel()
        self.srt_panel.entry_selected.connect(self.on_srt_selected)
        self.srt_panel.data_changed.connect(self.on_data_changed)
        self.srt_panel.file_dropped.connect(self.import_srt_from_drop)
        self.splitter.addWidget(self.srt_panel)

        # Set splitter proportions
        self.splitter.setSizes([700, 700])

        layout.addWidget(self.splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.vobsub_status = QLabel("VobSub: Not loaded")
        self.vobsub_status.setStyleSheet("padding: 0 10px;")
        self.status_bar.addWidget(self.vobsub_status)

        self.srt_status = QLabel("SRT: Not loaded")
        self.srt_status.setStyleSheet("padding: 0 10px;")
        self.status_bar.addWidget(self.srt_status)

        self.match_status = QLabel("Match: N/A")
        self.match_status.setStyleSheet("padding: 0 10px;")
        self.status_bar.addWidget(self.match_status)

        self.status_bar.addPermanentWidget(QLabel("Ready"))

        # Setup menu
        self.setup_menu()

    def setup_toolbar(self):
        """Setup toolbar with action buttons."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Import VobSub
        import_vobsub_btn = QPushButton("Import VobSub")
        import_vobsub_btn.setToolTip("Import IDX/SUB file (Ctrl+O)")
        import_vobsub_btn.clicked.connect(self.import_vobsub)
        toolbar.addWidget(import_vobsub_btn)

        # Import SRT
        import_srt_btn = QPushButton("Import SRT")
        import_srt_btn.setToolTip("Import SRT file (Ctrl+I)")
        import_srt_btn.clicked.connect(self.import_srt)
        toolbar.addWidget(import_srt_btn)

        toolbar.addSeparator()

        # Save SRT
        self.save_btn = QPushButton("Save SRT")
        self.save_btn.setToolTip("Save SRT file (Ctrl+S)")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_srt)
        toolbar.addWidget(self.save_btn)

        toolbar.addSeparator()

        # Compare button
        compare_btn = QPushButton("Compare")
        compare_btn.setToolTip("Compare subtitles and highlight differences")
        compare_btn.clicked.connect(self.compare_subtitles)
        toolbar.addWidget(compare_btn)

        toolbar.addSeparator()

        # OCR button
        self.ocr_btn = QPushButton("OCR")
        self.ocr_btn.setToolTip("Run OCR on VobSub images to generate SRT (Ctrl+R)")
        self.ocr_btn.setEnabled(False)
        self.ocr_btn.clicked.connect(self.run_ocr)
        toolbar.addWidget(self.ocr_btn)

        self.toolbar_buttons = {
            'import_vobsub': import_vobsub_btn,
            'import_srt': import_srt_btn,
            'save': self.save_btn,
            'ocr': self.ocr_btn,
        }

    def setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_vobsub_action = QAction("Open VobSub...", self)
        open_vobsub_action.setShortcut(QKeySequence.StandardKey.Open)
        open_vobsub_action.triggered.connect(self.import_vobsub)
        file_menu.addAction(open_vobsub_action)

        open_srt_action = QAction("Open SRT...", self)
        open_srt_action.setShortcut("Ctrl+I")
        open_srt_action.triggered.connect(self.import_srt)
        file_menu.addAction(open_srt_action)

        file_menu.addSeparator()

        save_action = QAction("Save SRT", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_srt)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save SRT As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_srt_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        add_entry_action = QAction("Add Entry", self)
        add_entry_action.setShortcut("Ctrl+N")
        add_entry_action.triggered.connect(self.add_entry)
        edit_menu.addAction(add_entry_action)

        delete_entry_action = QAction("Delete Entry", self)
        delete_entry_action.setShortcut("Ctrl+D")
        delete_entry_action.triggered.connect(self.delete_entry)
        edit_menu.addAction(delete_entry_action)

        edit_menu.addSeparator()

        compare_action = QAction("Compare Subtitles", self)
        compare_action.setShortcut("Ctrl+R")
        compare_action.triggered.connect(self.compare_subtitles)
        edit_menu.addAction(compare_action)

        ocr_action = QAction("Run OCR", self)
        ocr_action.setShortcut("Ctrl+Shift+O")
        ocr_action.triggered.connect(self.run_ocr)
        edit_menu.addAction(ocr_action)

        # Navigation menu
        nav_menu = menubar.addMenu("Navigation")

        sync_action = QAction("Sync Selection", self)
        sync_action.setShortcut("Ctrl+T")
        sync_action.triggered.connect(self.sync_selection)
        nav_menu.addAction(sync_action)

    def import_vobsub(self):
        """Import VobSub file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open VobSub File",
            self.settings.value('last_dir', ''),
            "VobSub Index Files (*.idx)"
        )

        if not file_path:
            return

        self.import_vobsub_from_drop(file_path)

    def import_vobsub_from_drop(self, file_path: str):
        """Import VobSub file from drag and drop."""
        self.settings.setValue('last_dir', str(Path(file_path).parent))

        # Get FPS from settings or ask user
        fps = self.settings.value('vobsub_fps', 'ntsc')

        # Reload with selected FPS
        if self.vobsub_panel.load_vobsub(file_path, fps):
            self.vobsub_path = file_path
            self.vobsub_status.setText(f"VobSub: {Path(file_path).name}")
            self.ocr_btn.setEnabled(True)
            self.compare_subtitles()

    def import_srt(self):
        """Import SRT file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SRT File",
            self.settings.value('last_dir', ''),
            "Subtitle Files (*.srt *.txt)"
        )

        if not file_path:
            return

        self.import_srt_from_drop(file_path)

    def import_srt_from_drop(self, file_path: str):
        """Import SRT file from drag and drop."""
        self.settings.setValue('last_dir', str(Path(file_path).parent))

        if self.srt_panel.load_srt(file_path):
            self.srt_path = file_path
            self.srt_status.setText(f"SRT: {Path(file_path).name}")
            self.save_btn.setEnabled(True)
            self.modified = False
            self.update_title()
            self.compare_subtitles()

    def save_srt(self):
        """Save SRT file."""
        if not self.srt_path:
            self.save_srt_as()
            return

        if self.srt_panel.save(self.srt_path):
            self.modified = False
            self.update_title()
            self.status_bar.showMessage(f"Saved: {self.srt_path}", 3000)
        else:
            QMessageBox.critical(self, "Error", "Failed to save SRT file.")

    def save_srt_as(self):
        """Save SRT file with new name."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save SRT File",
            self.srt_path or self.settings.value('last_dir', ''),
            "Subtitle Files (*.srt)"
        )

        if not file_path:
            return

        if not file_path.endswith('.srt'):
            file_path += '.srt'

        self.srt_path = file_path
        self.save_srt()

    def run_ocr(self):
        """Run OCR on VobSub images to generate SRT."""
        if not self.vobsub_panel.entries:
            QMessageBox.warning(self, "OCR", "No VobSub loaded. Please import VobSub first.")
            return

        # Ask for language
        from PyQt6.QtWidgets import QInputDialog
        languages = ['ch_tra', 'ch_sim', 'en', 'ja', 'ko']
        lang, ok = QInputDialog.getItem(
            self, "OCR Language", "Select language:", languages, 0, False
        )
        if not ok:
            return

        # Run OCR in background
        from PyQt6.QtCore import QThread, pyqtSignal

        class OCRWorker(QThread):
            progress = pyqtSignal(int, int)
            finished = pyqtSignal(list)
            error = pyqtSignal(str)

            def __init__(self, entries, parser, lang):
                super().__init__()
                self.entries = entries
                self.parser = parser
                self.lang = lang

            def run(self):
                try:
                    import easyocr
                    reader = easyocr.Reader([self.lang])

                    results = []
                    for i, entry in enumerate(self.entries):
                        self.progress.emit(i + 1, len(self.entries))

                        img = self.parser.get_image(entry)
                        if img:
                            # Save to temp file for EasyOCR
                            import tempfile
                            import os
                            tmp_path = None
                            try:
                                # Create temp file without context manager to avoid Windows file lock issues
                                fd, tmp_path = tempfile.mkstemp(suffix='.png')
                                os.close(fd)  # Close file descriptor immediately
                                img.save(tmp_path)
                                ocr_result = reader.readtext(tmp_path)
                                text = '\n'.join([r[1] for r in ocr_result])
                                results.append({
                                    'index': entry.index,
                                    'start_time': entry.start_time,
                                    'end_time': entry.end_time,
                                    'text': text
                                })
                            finally:
                                # Clean up temp file
                                if tmp_path and os.path.exists(tmp_path):
                                    try:
                                        os.unlink(tmp_path)
                                    except OSError:
                                        pass  # Ignore cleanup errors

                    self.finished.emit(results)
                except Exception as e:
                    self.error.emit(str(e))

        self.ocr_btn.setEnabled(False)
        self.status_bar.showMessage("Running OCR...")

        self.ocr_worker = OCRWorker(
            self.vobsub_panel.entries,
            self.vobsub_panel.parser,
            lang
        )
        self.ocr_worker.progress.connect(self.on_ocr_progress)
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_worker.start()

    def on_ocr_progress(self, current, total):
        """Update OCR progress."""
        self.status_bar.showMessage(f"Running OCR... {current}/{total}")

    def on_ocr_finished(self, results):
        """Handle OCR completion."""
        self.ocr_btn.setEnabled(True)
        self.status_bar.showMessage(f"OCR complete: {len(results)} subtitles recognized", 5000)

        # Load results into SRT panel
        from core.models import SRTEntry
        entries = []
        for r in results:
            entry = SRTEntry(
                index=r['index'],
                start_time=r['start_time'],
                end_time=r['end_time'],
                text=r['text']
            )
            entries.append(entry)

        self.srt_panel.load_entries(entries)
        self.srt_status.setText(f"SRT: OCR result ({len(entries)} entries)")
        self.save_btn.setEnabled(True)
        self.modified = True
        self.update_title()
        self.compare_subtitles()

    def on_ocr_error(self, error_msg):
        """Handle OCR error."""
        self.ocr_btn.setEnabled(True)
        QMessageBox.critical(self, "OCR Error", f"Failed to run OCR:\n{error_msg}")

        self.srt_path = file_path
        self.save_srt()

    def compare_subtitles(self):
        """Compare VobSub and SRT subtitles."""
        vobsub_entries = self.vobsub_panel.entries
        srt_entries = self.srt_panel.entries

        if not vobsub_entries or not srt_entries:
            self.match_status.setText("Match: N/A")
            return

        # Simple comparison logic
        matched = 0
        offset = 0
        missing = 0
        extra = 0

        max_len = max(len(vobsub_entries), len(srt_entries))

        for i in range(max_len):
            if i < len(vobsub_entries) and i < len(srt_entries):
                ventry = vobsub_entries[i]
                sentry = srt_entries[i]

                # Check time difference
                time_diff = abs(ventry.start_time - sentry.start_time)

                if time_diff < 100:  # Less than 100ms difference
                    self.srt_panel.set_match_status(sentry.index, 'normal')
                    matched += 1
                elif time_diff < 5000:  # Less than 5 seconds
                    self.srt_panel.set_match_status(sentry.index, 'offset')
                    offset += 1
                else:
                    self.srt_panel.set_match_status(sentry.index, 'missing')
                    missing += 1
            elif i < len(srt_entries):
                # Extra SRT entry
                sentry = srt_entries[i]
                self.srt_panel.set_match_status(sentry.index, 'extra')
                extra += 1
            else:
                # Missing SRT entry
                missing += 1

        self.match_status.setText(
            f"Match: {matched} OK, {offset} offset, {missing} missing, {extra} extra"
        )

    def on_vobsub_selected(self, index: int):
        """Handle VobSub entry selection."""
        self.srt_panel.select_entry(index)

    def on_srt_selected(self, index: int):
        """Handle SRT entry selection."""
        self.vobsub_panel.select_entry(index)

    def on_data_changed(self):
        """Handle data modification."""
        self.modified = True
        self.update_title()

    def update_title(self):
        """Update window title with modification status."""
        title = "SubtitleCompare - VobSub/SRT Comparison Tool"
        if self.srt_path:
            title += f" - {Path(self.srt_path).name}"
        if self.modified:
            title += " *"
        self.setWindowTitle(title)

    def sync_selection(self):
        """Sync selection between panels."""
        # Selection is already synced via signals
        pass

    def add_entry(self):
        """Add new entry."""
        # Get current selection and add after it
        pass

    def delete_entry(self):
        """Delete selected entry."""
        pass

    def load_settings(self):
        """Load application settings."""
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)

        state = self.settings.value('windowState')
        if state:
            self.restoreState(state)

    def save_settings(self):
        """Save application settings."""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())

    def closeEvent(self, event):
        """Handle window close event."""
        if self.modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before exiting?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                self.save_srt()
                if self.modified:  # Still modified (save failed)
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        self.save_settings()
        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("SubtitleCompare")
    app.setApplicationDisplayName("SubtitleCompare")

    # Set application-wide font
    from PyQt6.QtGui import QFont
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
