import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget
from gui_directory_tree import DirectoryTreePane
from gui_directory_details import DirectoryDetailsPane
from gui_files_grid import FilesGridPane
from constants import PUBLIC_ROOT, PRIVATE_ROOT, SAFE_DELETE_ROOT
from scroll_position_manager import ScrollPositionManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIFT Image Sorter")
        self.setGeometry(100, 100, 1200, 800)

        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Create panes
        self.directory_tree = DirectoryTreePane(PUBLIC_ROOT, PRIVATE_ROOT)
        self.directory_details = DirectoryDetailsPane(PUBLIC_ROOT, PRIVATE_ROOT, SAFE_DELETE_ROOT)
        self.files_grid = FilesGridPane(PUBLIC_ROOT, PRIVATE_ROOT, SAFE_DELETE_ROOT)  # Pass all required arguments

        # Add panes to layout with specified widths
        main_layout.addWidget(self.directory_tree, 15)
        main_layout.addWidget(self.directory_details, 15)
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