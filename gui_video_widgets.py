import cv2
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QStyle, QSizePolicy, QStackedWidget, QFrame
from PyQt6.QtGui import QPixmap, QImage, QColor, QIcon
from PyQt6.QtCore import Qt, QSize, QUrl, QPoint, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

class VideoThumbnailWidget(QWidget):
    sort_public = pyqtSignal(str)
    sort_private = pyqtSignal(str)
    clicked = pyqtSignal(str)  # New signal for when the widget is clicked

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.file_path = file_path
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.stacked_widget = QStackedWidget(self)
        layout.addWidget(self.stacked_widget)
        
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.stacked_widget.addWidget(self.thumbnail_label)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.stacked_widget.addWidget(self.video_widget)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setMuted(True)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)
        
        self.play_icon = QLabel(self)
        self.play_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        play_pixmap = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay).pixmap(32, 32)
        self.play_icon.setPixmap(play_pixmap)
        self.play_icon.setStyleSheet("background-color: rgba(0, 0, 0, 128);")
        
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

        self.public_button.clicked.connect(lambda: self.sort_public.emit(self.file_path))
        self.private_button.clicked.connect(lambda: self.sort_private.emit(self.file_path))
        
        self.create_thumbnail()
        
    def create_thumbnail(self):
        cap = cv2.VideoCapture(self.file_path)
        ret, frame = cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.pixmap = QPixmap.fromImage(qt_image)
            self.update_thumbnail()
        cap.release()

    def update_thumbnail(self):
        if hasattr(self, 'pixmap'):
            scaled_pixmap = self.pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.thumbnail_label.setPixmap(scaled_pixmap)

    def play(self):
        self.stacked_widget.setCurrentWidget(self.video_widget)
        self.play_icon.hide()
        self.media_player.play()

    def stop(self):
        self.media_player.stop()
        self.media_player.setPosition(0)
        self.stacked_widget.setCurrentWidget(self.thumbnail_label)
        self.play_icon.show()

    def cleanup(self):
        self.stop()
        self.media_player.setSource(QUrl())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_thumbnail()
        self.play_icon.setGeometry(0, 0, self.width(), self.height())
        self.hover_widget.setGeometry(0, self.height() - 30, self.width(), 30)

    def enterEvent(self, event):
        self.hover_widget.raise_()
        self.hover_widget.show()
        self.play()

    def leaveEvent(self, event):
        self.hover_widget.hide()
        self.stop()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.file_path)
        super().mousePressEvent(event)

class VideoPlayerWidget(QWidget):
    closed = pyqtSignal()
    sort_public = pyqtSignal(str)
    sort_private = pyqtSignal(str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setMouseTracking(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a frame to hold the close button and video widget
        frame = QFrame(self)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add close button to the top right
        close_button = QPushButton(self)
        close_button.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton)))
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("QPushButton { border: none; background-color: transparent; }")
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        frame_layout.addLayout(button_layout)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setMouseTracking(True)
        frame_layout.addWidget(self.video_widget)
        
        # Add Public and Private buttons
        self.public_button = QPushButton("Public")
        self.private_button = QPushButton("Private")
        self.public_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.private_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.public_button)
        buttons_layout.addWidget(self.private_button)
        buttons_layout.addStretch()
        
        frame_layout.addLayout(buttons_layout)
        
        # Add scrubbing bar
        self.scrubbing_bar = QSlider(Qt.Orientation.Horizontal)
        self.scrubbing_bar.setRange(0, 0)
        self.scrubbing_bar.sliderMoved.connect(self.set_position)
        self.scrubbing_bar.sliderPressed.connect(self.scrubbing_bar_pressed)
        frame_layout.addWidget(self.scrubbing_bar)
        
        # Add volume bar with icon
        volume_layout = QHBoxLayout()
        volume_icon = QPushButton()
        volume_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        volume_icon.setFixedSize(24, 24)
        volume_icon.setStyleSheet("background-color: transparent; border: none;")
        self.volume_bar = QSlider(Qt.Orientation.Horizontal)
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setValue(100)
        self.volume_bar.setFixedWidth(self.width() // 4)  # Set width to 25% of the video window
        self.volume_bar.valueChanged.connect(self.set_volume)
        
        volume_layout.addStretch()
        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_bar)
        frame_layout.addLayout(volume_layout)
        
        layout.addWidget(frame)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.mediaStatusChanged.connect(self.handle_media_status_changed)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.positionChanged.connect(self.update_position)
        
        # Connect sorting buttons
        self.public_button.clicked.connect(lambda: self.sort_public.emit(self.file_path))
        self.private_button.clicked.connect(lambda: self.sort_private.emit(self.file_path))
        
        # Auto-play when initialized
        self.media_player.play()

    def cleanup(self):
        self.media_player.stop()
        self.media_player.setSource(QUrl())

    def mousePressEvent(self, event):
        if self.video_widget.geometry().contains(event.pos()):
            relative_x = event.pos().x() - self.video_widget.pos().x()
            width = self.video_widget.width()
            if width > 0:
                position = int((relative_x / width) * self.media_player.duration())
                self.media_player.setPosition(position)
        super().mousePressEvent(event)

    def closeEvent(self, event):
        self.cleanup()
        self.closed.emit()
        super().closeEvent(event)

    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_player.setPosition(0)
            self.media_player.play()

    def load(self, file_path):
        self.file_path = file_path
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.play()

    def set_position(self, position):
        self.media_player.setPosition(position)

    def scrubbing_bar_pressed(self):
        position = self.scrubbing_bar.value()
        self.set_position(position)

    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100)

    def update_duration(self, duration):
        self.scrubbing_bar.setRange(0, duration)

    def update_position(self, position):
        if not self.scrubbing_bar.isSliderDown():
            self.scrubbing_bar.setValue(position)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.volume_bar.setFixedWidth(self.width() // 4)  # Update volume bar width on resize