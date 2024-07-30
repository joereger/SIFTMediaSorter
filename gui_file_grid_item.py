from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
from gui_video_widgets import VideoThumbnailWidget
import os

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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create hover buttons
        self.hover_widget = QWidget(self)
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
            self.content_widget = VideoThumbnailWidget(file_path, self)
        else:
            self.content_widget = ClickableLabel(self)
            self.content_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.pixmap = QPixmap(file_path)
            if self.pixmap.isNull():
                self.content_widget.setText(os.path.basename(file_path))
            else:
                self.adjust_content()

        layout.addWidget(self.content_widget)

    def adjust_content(self):
        if hasattr(self, 'pixmap') and not self.pixmap.isNull():
            scaled_pixmap = self.pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.content_widget.setPixmap(scaled_pixmap)
        if isinstance(self.content_widget, VideoThumbnailWidget):
            self.content_widget.setFixedSize(self.size())
        if hasattr(self, 'hover_widget'):
            self.hover_widget.setGeometry(0, self.height() - 30, self.width(), 30)

    def cleanup(self):
        if isinstance(self.content_widget, VideoThumbnailWidget):
            self.content_widget.cleanup()

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
        self.parent.sort_public(self.file_path)

    def sort_private(self):
        self.parent.sort_private(self.file_path)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_content()