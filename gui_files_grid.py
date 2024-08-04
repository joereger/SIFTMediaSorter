import os
from PyQt6.QtWidgets import QScrollArea, QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap
from gui_file_grid_item import FileGridItem
from sift_io_utils import SiftIOUtils
from gui_video_widgets import VideoPlayerWidget

class FilesGridPane(QScrollArea):
    file_selected = pyqtSignal(str)
    stats_updated = pyqtSignal(str)
    directory_removed = pyqtSignal(str)

    def __init__(self, public_root, private_root, safe_delete_root):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(5)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)

        self.zoomed_widget = QWidget()
        self.zoomed_layout = QVBoxLayout(self.zoomed_widget)
        self.zoomed_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.zoomed_layout.setContentsMargins(0, 0, 0, 0)
        self.zoomed_layout.setSpacing(10)

        self.zoomed_content = QLabel()
        self.zoomed_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoomed_layout.addWidget(self.zoomed_content)

        # Create persistent buttons for zoomed view
        self.button_widget = QWidget()
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.public_button = QPushButton("Public")
        self.private_button = QPushButton("Private")
        self.close_button = QPushButton("Close")

        self.public_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.private_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")

        self.button_layout.addWidget(self.public_button)
        self.button_layout.addWidget(self.private_button)
        self.button_layout.addWidget(self.close_button)

        self.zoomed_layout.addWidget(self.button_widget)

        self.stacked_widget.addWidget(self.grid_widget)
        self.stacked_widget.addWidget(self.zoomed_widget)

        self.current_path = ""
        self.current_file = ""
        self.items = []
        self.public_root = public_root
        self.private_root = private_root

        # Initialize SiftIOUtils
        self.sift_io = SiftIOUtils(public_root, private_root, safe_delete_root)

        # Connect button signals
        self.public_button.clicked.connect(self.sort_public_current)
        self.private_button.clicked.connect(self.sort_private_current)
        self.close_button.clicked.connect(self.close_zoomed)

    @pyqtSlot(str)
    def update_directory(self, path):
        if path != self.current_path:
            self.close_zoomed()
            self.current_path = path
            self.refresh_grid()

    def refresh_grid(self):
        self.clear_grid()
        if os.path.exists(self.current_path) and os.path.isdir(self.current_path):
            self.populate_grid()
        else:
            self.handle_directory_removal(self.current_path)

    def handle_directory_removal(self, removed_path):
        parent_dir = os.path.dirname(removed_path)
        if parent_dir == removed_path:  # We're at the root
            if removed_path.startswith(self.public_root):
                self.current_path = self.public_root
            else:
                self.current_path = self.private_root
        else:
            self.current_path = parent_dir
        
        self.directory_removed.emit(self.current_path)
        self.refresh_grid()

    def clear_grid(self):
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                if isinstance(widget, FileGridItem):
                    widget.cleanup()
                widget.setParent(None)
                widget.deleteLater()
        self.items = []

    def populate_grid(self):
        files = sorted([f for f in os.listdir(self.current_path) if os.path.isfile(os.path.join(self.current_path, f))])
        row, col = 0, 0
        for file in files:
            file_path = os.path.join(self.current_path, file)
            item = FileGridItem(file_path, self)
            item.file_clicked.connect(self.show_zoomed)
            self.items.append(item)
            self.grid_layout.addWidget(item, row, col)
            col += 1
            if col == 4:
                col = 0
                row += 1
        self.adjust_grid()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_grid()
        if self.stacked_widget.currentWidget() == self.zoomed_widget:
            self.show_zoomed(self.current_file)

    def adjust_grid(self):
        width = self.grid_widget.width()
        item_width = max(100, (width // 4) - self.grid_layout.spacing())
        for item in self.items:
            item.setFixedSize(item_width, item_width)
            item.adjust_content()
        self.grid_layout.update()

    def show_zoomed(self, file_path):
        self.file_selected.emit(file_path)
        self.current_file = file_path

        # Clear previous zoomed content
        self.zoomed_content.clear()

        # Create zoomed view
        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() in ['.mp4', '.avi', '.mov', '.wmv', '.mpg', '.mpeg']:
            video_player = VideoPlayerWidget(file_path)
            video_player.closed.connect(self.close_zoomed)
            video_player.sort_public.connect(self.sort_public_current)
            video_player.sort_private.connect(self.sort_private_current)
            self.zoomed_layout.insertWidget(0, video_player)
            self.public_button.hide()
            self.private_button.hide()
        else:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.viewport().width() - 20,
                    self.viewport().height() - 100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.zoomed_content.setPixmap(scaled_pixmap)
            else:
                self.zoomed_content.setText(f"Unable to display: {os.path.basename(file_path)}")
            self.public_button.show()
            self.private_button.show()

        self.close_button.show()
        self.stacked_widget.setCurrentWidget(self.zoomed_widget)

    def close_zoomed(self):
        self.stacked_widget.setCurrentWidget(self.grid_widget)
        # Remove any video player widget if it exists
        for i in reversed(range(self.zoomed_layout.count())):
            widget = self.zoomed_layout.itemAt(i).widget()
            if isinstance(widget, VideoPlayerWidget):
                widget.setParent(None)
                widget.deleteLater()

    def sort_public_current(self):
        self.sort_public(self.current_file)

    def sort_private_current(self):
        self.sort_private(self.current_file)

    def sort_public(self, file_path):
        self.sift_io.sort_file(file_path, True)
        self.close_zoomed()
        self.refresh_grid()
        self.stats_updated.emit(os.path.dirname(file_path))

    def sort_private(self, file_path):
        self.sift_io.sort_file(file_path, False)
        self.close_zoomed()
        self.refresh_grid()
        self.stats_updated.emit(os.path.dirname(file_path))

    def refresh_metadata(self, path):
        if path == self.current_path:
            for item in self.items:
                item.update_border()
        self.adjust_grid()