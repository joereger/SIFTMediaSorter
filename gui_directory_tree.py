from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTreeView, QStyledItemDelegate, QPushButton
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QPainter, QIcon
from PyQt6.QtCore import pyqtSignal, Qt, QRect, QSize, QModelIndex, QEvent
import os
from sift_io_utils import SiftIOUtils

class DirectoryTreePane(QWidget):
    directory_selected = pyqtSignal(str)
    directory_refreshed = pyqtSignal(str)

    def __init__(self, public_root, private_root):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.public_tree = DirectoryTree(public_root)
        self.private_tree = DirectoryTree(private_root)

        self.tab_widget.addTab(self.public_tree, "Public")
        self.tab_widget.addTab(self.private_tree, "Private")

        self.public_tree.directory_selected.connect(self.directory_selected)
        self.private_tree.directory_selected.connect(self.directory_selected)
        self.public_tree.directory_refreshed.connect(self.directory_refreshed)
        self.private_tree.directory_refreshed.connect(self.directory_refreshed)

    def update_directory(self, path):
        self.public_tree.update_directory(path)
        self.private_tree.update_directory(path)

    def refresh_stats(self, path):
        current_tree = self.tab_widget.currentWidget()
        current_tree.refresh_stats(path)

class ProgressBarDelegate(QStyledItemDelegate):
    refresh_clicked = pyqtSignal(QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.refresh_icon = QIcon.fromTheme("view-refresh")

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        progress = index.data(Qt.ItemDataRole.UserRole + 1)
        if progress is not None:
            rect = option.rect
            bar_width = 30
            bar_height = 5
            icon_size = 16

            # Position the bar to the right of the text, aligned to the right side of the window
            bar_rect = QRect(
                rect.right() - bar_width - icon_size - 10,  # 10 pixels padding from the right edge
                rect.top() + (rect.height() - bar_height) // 2,
                bar_width,
                bar_height
            )

            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw background
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.drawRect(bar_rect)

            # Draw progress
            progress_width = int(bar_width * progress)
            progress_rect = QRect(bar_rect)
            progress_rect.setWidth(progress_width)
            painter.setBrush(QBrush(QColor(0, 255, 0)))
            painter.drawRect(progress_rect)

            # Draw refresh icon
            icon_rect = QRect(
                rect.right() - icon_size - 5,  # 5 pixels padding from the right edge
                rect.top() + (rect.height() - icon_size) // 2,
                icon_size,
                icon_size
            )
            self.refresh_icon.paint(painter, icon_rect)

            painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            rect = option.rect
            icon_size = 16
            icon_rect = QRect(
                rect.right() - icon_size - 5,
                rect.top() + (rect.height() - icon_size) // 2,
                icon_size,
                icon_size
            )
            if icon_rect.contains(event.pos()):
                self.refresh_clicked.emit(index)
                return True
        return super().editorEvent(event, model, option, index)

class DirectoryTree(QTreeView):
    directory_selected = pyqtSignal(str)
    directory_refreshed = pyqtSignal(str)

    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.setHeaderHidden(True)
        self.clicked.connect(self.item_clicked)
        self.delegate = ProgressBarDelegate()
        self.delegate.refresh_clicked.connect(self.refresh_directory)
        self.setItemDelegate(self.delegate)
        self.sift_io_utils = SiftIOUtils(root_path, root_path, "")  # Assume same root for public and private
        self.populate_tree()

    def populate_tree(self):
        self.model.clear()
        root_item = self.model.invisibleRootItem()
        self.add_directory(root_item, self.root_path)

    def add_directory(self, parent_item, path):
        dir_item = QStandardItem(os.path.basename(path))
        dir_item.setData(path, Qt.ItemDataRole.UserRole)
        progress = self.calculate_progress(path)
        dir_item.setData(progress, Qt.ItemDataRole.UserRole + 1)
        parent_item.appendRow(dir_item)
        
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    self.add_directory(dir_item, item_path)
        except FileNotFoundError:
            parent_item.removeRow(dir_item.row())

    def calculate_progress(self, path):
        status = self.sift_io_utils.get_directory_status(path)
        if status['total'] == 0:
            return 0
        return status['reviewed'] / status['total']

    def item_clicked(self, index):
        item = self.model.itemFromIndex(index)
        if item is not None:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path is not None:
                self.directory_selected.emit(path)

    def update_directory(self, path):
        if not os.path.exists(path):
            self.handle_directory_removal(path)
        else:
            self.refresh_directory_structure()

    def handle_directory_removal(self, removed_path):
        parent_path = os.path.dirname(removed_path)
        if parent_path == removed_path or parent_path == self.root_path:
            self.refresh_directory_structure()
            self.directory_selected.emit(self.root_path)
        else:
            self.refresh_directory_structure()
            self.directory_selected.emit(parent_path)

    def refresh_directory_structure(self):
        current_index = self.currentIndex()
        current_path = current_index.data(Qt.ItemDataRole.UserRole) if current_index.isValid() else self.root_path
        self.populate_tree()
        self.select_path(current_path)

    def select_path(self, path):
        if not os.path.exists(path):
            path = os.path.dirname(path)
        item = self.find_item_by_path(path)
        if item:
            self.setCurrentIndex(item.index())
        else:
            self.setCurrentIndex(self.model.index(0, 0))

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

    def refresh_stats(self, path):
        item = self.find_item_by_path(path)
        if item:
            progress = self.calculate_progress(path)
            item.setData(progress, Qt.ItemDataRole.UserRole + 1)
            self.model.dataChanged.emit(item.index(), item.index())

        # Refresh parent directories
        parent_path = os.path.dirname(path)
        if parent_path != path and parent_path.startswith(self.root_path):
            self.refresh_stats(parent_path)

    def refresh_directory(self, index):
        item = self.model.itemFromIndex(index)
        if item is not None:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path is not None:
                self.refresh_directory_recursive(path)
                self.directory_refreshed.emit(path)

    def refresh_directory_recursive(self, path):
        # Refresh the directory structure
        self.refresh_directory_structure()
        
        # Refresh the status of the current directory
        self.refresh_stats(path)

        # Refresh subdirectories
        for root, dirs, files in os.walk(path):
            for dir_name in dirs:
                subdir_path = os.path.join(root, dir_name)
                self.refresh_stats(subdir_path)

        # Update the view
        self.viewport().update()