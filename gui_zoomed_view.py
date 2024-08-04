from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QSizePolicy, QToolButton)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from gui_video_widgets import VideoPlayerWidget
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class ZoomedView(QWidget):
    stats_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)

        self.content = None
        self.current_file_path = None
        self.sift_io = None
        self.sift_metadata = None

    def show_zoomed(self, file_path, sift_io, sift_metadata):
        self.current_file_path = file_path
        self.sift_io = sift_io
        self.sift_metadata = sift_metadata

        if self.content:
            self.content.setParent(None)
            self.content.deleteLater()

        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() in ['.mp4', '.avi', '.mov', '.wmv', '.mpg', '.mpeg']:
            self.content = VideoPlayerWidget(file_path)
            self.content.closed.connect(self.close_zoomed)
            self.content.public_button.clicked.connect(self.sort_public)
            self.content.private_button.clicked.connect(self.sort_private)
        else:
            self.content = QWidget()
            content_layout = QVBoxLayout(self.content)
            
            # Create a container for the image and close button
            top_container = QWidget()
            top_layout = QHBoxLayout(top_container)
            top_layout.setContentsMargins(0, 0, 0, 0)
            
            self.image_label = ClickableLabel()
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.image_label.clicked.connect(self.close_zoomed)
            
            close_button = QToolButton()
            close_button.setIcon(QIcon.fromTheme("window-close"))
            close_button.setIconSize(QSize(32, 32))
            close_button.setStyleSheet("QToolButton { border: none; background: transparent; }")
            close_button.clicked.connect(self.close_zoomed)
            close_button.setCursor(Qt.CursorShape.PointingHandCursor)
            
            top_layout.addWidget(self.image_label)
            top_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            
            content_layout.addWidget(top_container)
            
            # Create buttons
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            self.public_button = QPushButton("Public")
            self.private_button = QPushButton("Private")
            self.public_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            self.private_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
            self.public_button.clicked.connect(self.sort_public)
            self.private_button.clicked.connect(self.sort_private)
            button_layout.addWidget(self.public_button)
            button_layout.addWidget(self.private_button)
            
            content_layout.addWidget(button_container)
            
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText(f"Unable to load: {os.path.basename(file_path)}")

        self.layout.addWidget(self.content)

    def close_zoomed(self):
        if self.content:
            if isinstance(self.content, VideoPlayerWidget):
                self.content.cleanup()
            self.content.setParent(None)
            self.content.deleteLater()
            self.content = None
        self.hide()

    def sort_public(self):
        if self.current_file_path:
            self.sift_io.sort_file(self.current_file_path, True)
            self.sift_metadata.update_manual_review_status(self.current_file_path, 'public')
            logging.debug(f"Sorted {self.current_file_path} as public")
            self.stats_updated.emit(os.path.dirname(self.current_file_path))
        self.close_zoomed()

    def sort_private(self):
        if self.current_file_path:
            self.sift_io.sort_file(self.current_file_path, False)
            self.sift_metadata.update_manual_review_status(self.current_file_path, 'private')
            logging.debug(f"Sorted {self.current_file_path} as private")
            self.stats_updated.emit(os.path.dirname(self.current_file_path))
        self.close_zoomed()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if isinstance(self.content, QWidget) and hasattr(self, 'image_label'):
            pixmap = self.image_label.pixmap()
            if pixmap and not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)