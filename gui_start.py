import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from gui_directory_tree import DirectoryTreePane
from gui_directory_details import DirectoryDetailsPane
from gui_files_grid import FilesGridPane

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIFT Image Sorter")
        self.setWindowState(Qt.WindowState.WindowMaximized)

        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Create left side widget and layout
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        # Create panes
        self.directory_details = DirectoryDetailsPane()
        self.directory_tree = DirectoryTreePane()
        self.files_grid = FilesGridPane()

        # Add directory details and directory tree to left layout
        left_layout.addWidget(self.directory_details, 25)
        left_layout.addWidget(self.directory_tree, 75)

        # Add left widget and files grid to main layout
        main_layout.addWidget(left_widget, 30)
        main_layout.addWidget(self.files_grid, 70)

        # Connect signals
        self.directory_tree.directory_selected.connect(self.on_directory_selected)
        self.directory_tree.directory_refreshed.connect(self.on_directory_refreshed)
        self.files_grid.directory_removed.connect(self.on_directory_removed)
        self.files_grid.stats_updated.connect(self.directory_tree.refresh_stats)
        self.directory_details.directory_sorted.connect(self.on_directory_sorted)

    def on_directory_selected(self, path):
        self.directory_details.update_directory(path)
        self.files_grid.update_directory(path)

    def on_directory_removed(self, path):
        self.directory_tree.update_directory(path)
        self.directory_details.update_directory(path)
        self.files_grid.update_directory(path)

    def on_directory_refreshed(self, path):
        self.directory_details.update_directory(path)
        self.files_grid.update_directory(path)

    def on_directory_sorted(self, path):
        self.directory_tree.refresh_stats(path)
        self.files_grid.refresh_metadata(path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())