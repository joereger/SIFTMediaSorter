from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTreeView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import pyqtSignal, Qt
import os

class DirectoryTreePane(QWidget):
    directory_selected = pyqtSignal(str)

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

    def update_directory(self, path):
        self.public_tree.update_directory(path)
        self.private_tree.update_directory(path)

    def refresh_stats(self, path):
        current_tree = self.tab_widget.currentWidget()
        current_tree.refresh_stats(path)

class DirectoryTree(QTreeView):
    directory_selected = pyqtSignal(str)

    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.setHeaderHidden(True)
        self.clicked.connect(self.item_clicked)
        self.populate_tree()

    def populate_tree(self):
        self.model.clear()
        root_item = self.model.invisibleRootItem()
        self.add_directory(root_item, self.root_path)

    def add_directory(self, parent_item, path):
        dir_item = QStandardItem(os.path.basename(path))
        dir_item.setData(path, Qt.ItemDataRole.UserRole)
        parent_item.appendRow(dir_item)
        
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    self.add_directory(dir_item, item_path)
        except FileNotFoundError:
            parent_item.removeRow(dir_item.row())

    def item_clicked(self, index):
        item = self.model.itemFromIndex(index)
        path = item.data(Qt.ItemDataRole.UserRole)
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
            self.model.dataChanged.emit(item.index(), item.index())