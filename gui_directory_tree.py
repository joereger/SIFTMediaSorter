from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTreeView, QStyledItemDelegate, QStyle, QScrollBar
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPainter, QColor, QFont, QPen
from PyQt6.QtCore import pyqtSignal, Qt, QRect, QSize
import os
from sift_io_utils import SiftIOUtils

class ProgressBarDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        # Draw progress bar
        progress = index.data(Qt.ItemDataRole.UserRole + 1)
        if progress is not None:
            rect = option.rect
            progress_rect = QRect(
                int(rect.right() - rect.width() * 0.15),
                rect.y() + (rect.height() - 10) // 2,  # Center vertically
                int(rect.width() * 0.15),
                10  # Set height to 10 pixels
            )
            
            # Background
            painter.fillRect(progress_rect, QColor(200, 200, 200))  # Gray background
            
            # Progress
            progress_width = int(progress_rect.width() * progress)
            painter.fillRect(QRect(progress_rect.left(), progress_rect.top(), progress_width, progress_rect.height()), QColor(0, 255, 0))  # Green progress

            # Draw border
            pen = QPen(QColor(100, 100, 100))  # Dark gray border
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(progress_rect)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QSize(size.width(), max(size.height(), 20))  # Ensure minimum height for progress bar

class DirectoryTreePane(QWidget):
    directory_selected = pyqtSignal(str)

    def __init__(self, public_root, private_root):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create Public and Private tabs
        self.public_tree = DirectoryTree(public_root)
        self.private_tree = DirectoryTree(private_root)

        self.tab_widget.addTab(self.public_tree, "Public")
        self.tab_widget.addTab(self.private_tree, "Private")

        # Connect signals
        self.public_tree.directory_selected.connect(self.directory_selected)
        self.private_tree.directory_selected.connect(self.directory_selected)

    def refresh_stats(self, path):
        self.public_tree.refresh_stats(path)
        self.private_tree.refresh_stats(path)

class DirectoryTree(QTreeView):
    directory_selected = pyqtSignal(str)

    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.setHeaderHidden(True)
        self.clicked.connect(self.item_clicked)
        self.setItemDelegate(ProgressBarDelegate(self))
        self.sift_io_utils = SiftIOUtils(root_path, root_path, os.path.join(root_path, 'safe_delete'))
        self.populate_tree()
        self.scroll_positions = {}  # Dictionary to store scroll positions

    def populate_tree(self):
        root_item = self.model.invisibleRootItem()
        self.add_directory(root_item, self.root_path)

    def add_directory(self, parent_item, path):
        dir_item = QStandardItem(os.path.basename(path))
        dir_item.setData(path, Qt.ItemDataRole.UserRole)
        
        # Initialize progress to zero until data is loaded
        dir_item.setData(0, Qt.ItemDataRole.UserRole + 1)
        
        parent_item.appendRow(dir_item)
        
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                self.add_directory(dir_item, item_path)

    def item_clicked(self, index):
        item = self.model.itemFromIndex(index)
        path = item.data(Qt.ItemDataRole.UserRole)
        
        # Skip initializing data for the root directory
        if path == self.root_path:
            return
        
        # Save current scroll position
        self.save_scroll_position(self.currentIndex().data(Qt.ItemDataRole.UserRole))

        # Load metadata for the selected directory
        self.update_directory_stats(item)
        
        self.directory_selected.emit(path)

        # Restore scroll position for the new directory
        self.restore_scroll_position(path)

    def save_scroll_position(self, path):
        if path:
            self.scroll_positions[path] = self.verticalScrollBar().value()

    def restore_scroll_position(self, path):
        if path in self.scroll_positions:
            self.verticalScrollBar().setValue(self.scroll_positions[path])
        else:
            self.verticalScrollBar().setValue(0)  # Ensure the scrollbar is set to the top if no saved position

    def currentChanged(self, current, previous):
        super().currentChanged(current, previous)
        if previous.isValid():
            self.model.itemFromIndex(previous).setFont(QFont())
        if current.isValid():
            font = QFont()
            font.setBold(True)
            self.model.itemFromIndex(current).setFont(font)
        self.viewport().update()

    def update_directory_stats(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        status = self.sift_io_utils.get_directory_status(path)
        total_files = status['total']
        progress = status['reviewed'] / total_files if total_files > 0 else 0
        item.setData(progress, Qt.ItemDataRole.UserRole + 1)

    def refresh_stats(self, path):
        item = self.find_item_by_path(path)
        if item:
            self.update_directory_stats(item)
            parent = item.parent()
            while parent:
                self.update_directory_stats(parent)
                parent = parent.parent()
        self.viewport().update()

    def find_item_by_path(self, path):
        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            found_item = self.find_item_recursive(item, path)
            if found_item:
                return found_item
        return None

    def find_item_recursive(self, item, path):
        if item.data(Qt.ItemDataRole.UserRole) == path:
            return item
        for row in range(item.rowCount()):
            child = item.child(row)
            found_item = self.find_item_recursive(child, path)
            if found_item:
                return found_item
        return None