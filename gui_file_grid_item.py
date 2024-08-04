from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from gui_video_widgets import VideoThumbnailWidget
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class FileGridItem(QWidget):
    file_clicked = pyqtSignal(str)

    def __init__(self, file_path, parent):
        super().__init__()
        self.file_path = file_path
        self.parent = parent
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.border_widget = QWidget(self)
        self.border_layout = QVBoxLayout(self.border_widget)
        self.border_layout.setContentsMargins(5, 5, 5, 5)
        self.border_layout.setSpacing(0)

        self.content_widget = QWidget(self.border_widget)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Create hover buttons
        self.hover_widget = QWidget(self.content_widget)
        hover_layout = QHBoxLayout(self.hover_widget)
        hover_layout.setContentsMargins(0, 0, 0, 0)
        hover_layout.setSpacing(0)
        self.public_button = QPushButton("Public")
        self.private_button = QPushButton("Private")
        self.public_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.private_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        hover_layout.addWidget(self.public_button)
        hover_layout.addWidget(self.private_button)
        self.hover_widget.setFixedHeight(30)
        self.hover_widget.hide()

        self.public_button.clicked.connect(self.sort_public)
        self.private_button.clicked.connect(self.sort_private)

        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() in ['.mp4', '.avi', '.mov', '.wmv', '.mpg', '.mpeg']:
            self.image_widget = VideoThumbnailWidget(file_path, self)
        else:
            self.image_widget = ClickableLabel(self)
            self.image_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.image_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.pixmap = QPixmap(file_path)
            if self.pixmap.isNull():
                self.image_widget.setText(os.path.basename(file_path))
            else:
                self.adjust_content()

        self.content_layout.addWidget(self.image_widget)
        self.border_layout.addWidget(self.content_widget)
        self.main_layout.addWidget(self.border_widget)

        self.update_border()

    def update_border(self):
        try:
            is_reviewed = self.parent.sift_io.get_file_review_status(self.file_path)
            if not is_reviewed:
                self.border_widget.setStyleSheet("QWidget { border: 5px solid gray; background-color: transparent; }")
            else:
                status = 'public' if self.parent.sift_io.get_file_review_status(self.file_path) else 'private'
                if status == 'public':
                    self.border_widget.setStyleSheet("QWidget { border: 5px solid #4CAF50; background-color: transparent; }")  # Green border
                elif status == 'private':
                    self.border_widget.setStyleSheet("QWidget { border: 5px solid #F44336; background-color: transparent; }")  # Red border
                else:
                    self.border_widget.setStyleSheet("QWidget { border: none; background-color: transparent; }")
        except Exception as e:
            logging.error(f"Error updating border for {self.file_path}: {str(e)}")
            self.border_widget.setStyleSheet("QWidget { border: 5px solid yellow; background-color: transparent; }")  # Yellow border for error

    def adjust_content(self):
        if hasattr(self, 'pixmap') and not self.pixmap.isNull():
            scaled_pixmap = self.pixmap.scaled(self.size() - QSize(20, 20), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_widget.setPixmap(scaled_pixmap)
        if isinstance(self.image_widget, VideoThumbnailWidget):
            self.image_widget.setFixedSize(self.size() - QSize(20, 20))
        if hasattr(self, 'hover_widget'):
            self.hover_widget.setGeometry(0, self.height() - 35, self.width(), 30)

    def cleanup(self):
        if isinstance(self.image_widget, VideoThumbnailWidget):
            self.image_widget.cleanup()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.file_clicked.emit(self.file_path)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.hover_widget.raise_()
        self.hover_widget.show()

    def leaveEvent(self, event):
        self.hover_widget.hide()

    def sort_public(self):
        try:
            self.parent.sort_public(self.file_path)
            self.update_border()
        except Exception as e:
            logging.error(f"Error sorting {self.file_path} as public: {str(e)}")

    def sort_private(self):
        try:
            self.parent.sort_private(self.file_path)
            self.update_border()
        except Exception as e:
            logging.error(f"Error sorting {self.file_path} as private: {str(e)}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_content()