from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSlot, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
import os
from sift_io_utils import SiftIOUtils
from sift_metadata_utils import SiftMetadataUtils

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

        # Initialize SiftIOUtils and SiftMetadataUtils
        self.io_utils = SiftIOUtils(public_root, private_root, safe_delete_root)
        self.metadata_utils = SiftMetadataUtils(public_root, private_root)

        self.current_path = None

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

    def sort_public(self):
        print("sort_public method called")
        if self.current_path:
            print(f"Sorting {self.current_path} as public")
            self.io_utils.batch_sort_directory(self.current_path, True)
            sorted_path = self.current_path
            if not os.path.exists(self.current_path):
                self.current_path = os.path.dirname(self.current_path)
                print(f"Directory no longer exists, new current_path: {self.current_path}")
            self.refresh_stats()
            print(f"Emitting directory_sorted signal with path: {sorted_path}")
            self.directory_sorted.emit(sorted_path)
        else:
            print("No current_path set, cannot sort")

    def sort_private(self):
        print("sort_private method called")
        if self.current_path:
            print(f"Sorting {self.current_path} as private")
            self.io_utils.batch_sort_directory(self.current_path, False)
            sorted_path = self.current_path
            if not os.path.exists(self.current_path):
                self.current_path = os.path.dirname(self.current_path)
                print(f"Directory no longer exists, new current_path: {self.current_path}")
            self.refresh_stats()
            print(f"Emitting directory_sorted signal with path: {sorted_path}")
            self.directory_sorted.emit(sorted_path)
        else:
            print("No current_path set, cannot sort")