from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QApplication
from PyQt6.QtCore import pyqtSlot, pyqtSignal, QThread, Qt
from PyQt6.QtGui import QColor, QPalette
import os
import logging
from sift_io_utils import SiftIOUtils

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SortWorker(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, io_utils, path, is_public):
        super().__init__()
        self.io_utils = io_utils
        self.path = path
        self.is_public = is_public
        self.is_running = True

    def run(self):
        try:
            self.io_utils.batch_sort_directory(self.path, self.is_public, self.progress.emit)
            if self.is_running:
                self.finished.emit()
        except Exception as e:
            logging.error(f"Error in SortWorker: {str(e)}")
            self.error.emit(str(e))

    def stop(self):
        self.is_running = False

class DirectoryDetailsPane(QWidget):
    directory_sorted = pyqtSignal(str)

    def __init__(self, public_root, private_root, safe_delete_root):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.dir_name_label = QLabel("No directory selected")
        self.file_count_label = QLabel("")
        
        button_layout = QHBoxLayout()
        self.public_button = QPushButton("Public")
        self.private_button = QPushButton("Private")
        button_layout.addWidget(self.public_button)
        button_layout.addWidget(self.private_button)

        # Set button colors
        self.public_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.private_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")

        layout.addWidget(self.dir_name_label)
        layout.addWidget(self.file_count_label)
        layout.addLayout(button_layout)
        layout.addStretch()

        # Connect buttons to slots
        self.public_button.clicked.connect(self.sort_public)
        self.private_button.clicked.connect(self.sort_private)

        # Initialize SiftIOUtils
        self.io_utils = SiftIOUtils(public_root, private_root, safe_delete_root)

        self.current_path = None
        self.sort_worker = None

    @pyqtSlot(str)
    def update_directory(self, path):
        self.current_path = path
        self.refresh_stats()

    def refresh_stats(self):
        if self.current_path and os.path.exists(self.current_path):
            self.dir_name_label.setText(f"Directory: {self.current_path}")
            
            status = self.io_utils.get_directory_status(self.current_path)
            total_files = status['total']
            reviewed_files = status['reviewed']
            self.file_count_label.setText(f"Files: {reviewed_files}/{total_files} reviewed")
        else:
            self.dir_name_label.setText("No directory selected")
            self.file_count_label.setText("")

    def batch_sort(self, is_public):
        if self.current_path:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.public_button.setEnabled(False)
            self.private_button.setEnabled(False)
            
            self.sort_worker = SortWorker(self.io_utils, self.current_path, is_public)
            self.sort_worker.finished.connect(self.on_sort_finished)
            self.sort_worker.progress.connect(self.update_progress)
            self.sort_worker.error.connect(self.on_sort_error)
            self.sort_worker.start()
        else:
            logging.warning("No current_path set, cannot sort")

    def on_sort_finished(self):
        QApplication.restoreOverrideCursor()
        self.public_button.setEnabled(True)
        self.private_button.setEnabled(True)
        self.refresh_stats()
        self.directory_sorted.emit(self.current_path)
        self.sort_worker = None
        logging.info("Sorting finished successfully")

    def on_sort_error(self, error_message):
        QApplication.restoreOverrideCursor()
        self.public_button.setEnabled(True)
        self.private_button.setEnabled(True)
        logging.error(f"Sorting error: {error_message}")
        # Here you might want to show an error message to the user
        self.sort_worker = None

    def update_progress(self, value):
        # Update progress bar or status message
        logging.info(f"Sorting progress: {value}%")

    def sort_public(self):
        self.batch_sort(True)

    def sort_private(self):
        self.batch_sort(False)

    def closeEvent(self, event):
        if self.sort_worker and self.sort_worker.isRunning():
            self.sort_worker.stop()
            self.sort_worker.wait()
        super().closeEvent(event)