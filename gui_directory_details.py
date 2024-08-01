from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QColor, QPalette
import os
from sift_io_utils import SiftIOUtils
from sift_metadata_utils import SiftMetadataUtils

class DirectoryDetailsPane(QWidget):
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

        # Initialize SiftIOUtils and SiftMetadataUtils
        self.io_utils = SiftIOUtils(public_root, private_root, safe_delete_root)
        self.metadata_utils = SiftMetadataUtils(public_root, private_root)

        self.current_path = None

    @pyqtSlot(str)
    def update_directory(self, path):
        self.current_path = path
        self.refresh_stats()

    def refresh_stats(self):
        if self.current_path:
            self.dir_name_label.setText(f"Directory: {self.current_path}")
            
            status = self.io_utils.get_directory_status(self.current_path)
            total_files = status['total']
            reviewed_files = status['reviewed']
            self.file_count_label.setText(f"Files: {reviewed_files}/{total_files} reviewed")

    def sort_public(self):
        if self.current_path:
            self.io_utils.batch_sort_directory(self.current_path, True)
            self.refresh_stats()

    def sort_private(self):
        if self.current_path:
            self.io_utils.batch_sort_directory(self.current_path, False)
            self.refresh_stats()