import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from gui_directory_tree import DirectoryTreePane
from gui_directory_details import DirectoryDetailsPane
from gui_files_grid import FilesGridPane
from constants import PUBLIC_ROOT, PRIVATE_ROOT, SAFE_DELETE_ROOT
from scroll_position_manager import ScrollPositionManager

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
        self.directory_details = DirectoryDetailsPane(PUBLIC_ROOT, PRIVATE_ROOT, SAFE_DELETE_ROOT)
        self.directory_tree = DirectoryTreePane(PUBLIC_ROOT, PRIVATE_ROOT)
        self.files_grid = FilesGridPane(PUBLIC_ROOT, PRIVATE_ROOT, SAFE_DELETE_ROOT)

        # Add directory details and directory tree to left layout
        left_layout.addWidget(self.directory_details, 25)
        left_layout.addWidget(self.directory_tree, 75)

        # Add left widget and files grid to main layout
        main_layout.addWidget(left_widget, 30)
        main_layout.addWidget(self.files_grid, 70)

        # Connect signals
        self.directory_tree.directory_selected.connect(self.directory_details.update_directory)
        self.directory_tree.directory_selected.connect(self.files_grid.update_directory)

        # Initialize ScrollPositionManager
        self.scroll_manager = ScrollPositionManager()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())