from PyQt5.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton
#import QSlider, Style, Qt
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSlider, QStyle
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
#
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, QTimer
from PIL.ImageQt import ImageQt

from client.client import Client
#from utils.video_stream import VideoStream

import pyaudio


class ClientWindow(QMainWindow):
    _update_image_signal = pyqtSignal()
    _update_audio_signal = pyqtSignal()

    def __init__(
            self,
            file_name: str,
            host_address: str,
            host_port: int,
            rtp_port_v: int,
            rtp_port_a: int,
            parent=None):
        super(ClientWindow, self).__init__(parent)
        self.nframe = 0
        self.video_player = QLabel()
        self.play_button = QPushButton()
        self.state = 'pause'

        self.positionSlider = QSlider(Qt.Horizontal, self)
        self.positionSlider.setRange(0, 10)
        self.positionSlider.setValue(2)
        #self.positionSlider.sliderMoved.connect(self.setPosition)
        self.positionSlider.valueChanged.connect(self.valuechange)
        

        self.setup_button = QPushButton()
        self.tear_button = QPushButton()
        self.error_label = QLabel()

        self._media_client = Client(file_name, host_address, host_port, rtp_port_v, rtp_port_a)
        self._update_image_signal.connect(self.update_image)
        self._update_image_timer = QTimer()
        self._update_image_timer.timeout.connect(self._update_image_signal.emit)

        self._update_audio_signal.connect(self.update_audio)
        self._update_audio_timer = QTimer()
        self._update_audio_timer.timeout.connect(self._update_audio_signal.emit)

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        videoWidget = QVideoWidget()

        self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        #self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handle_error)

        self.stream = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Client")


        self.play_button.setEnabled(False)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.handle_play)

        self.setup_button.setEnabled(True)
        self.setup_button.setText('Setup')
        self.setup_button.clicked.connect(self.handle_setup)

        self.tear_button.setEnabled(False)
        self.tear_button.setText('Teardown')
        self.tear_button.clicked.connect(self.handle_teardown)

        self.error_label.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Maximum)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.positionSlider)
        control_layout.addWidget(self.setup_button)
        control_layout.addWidget(self.tear_button)

        layout = QVBoxLayout()
        layout.addWidget(self.video_player)
        layout.addLayout(control_layout)
        layout.addWidget(self.error_label)

        central_widget.setLayout(layout)

    def update_image(self):
        if not self._media_client.is_playing:
            return

        if self._media_client.time_stamp_v / self._media_client.fps_v > self._media_client.time_stamp_a / (self._media_client.fps_a/1) + 0.01:
            return

        frame = self._media_client.get_next_frame(type = 1)
        #frame = self._media_client.get_next_frame(type=2)

        #frame , timestamp= self._media_client.get_next_frame()
        #self.positionSlider.setValue(timestamp)
        if frame is not None:
            print("received frame!")
            pix = QPixmap.fromImage(ImageQt(frame[0]).copy())
            self.video_player.setPixmap(pix)
            self._media_client.time_stamp_v += 1

    def update_audio(self):
        if not self._media_client.is_playing:
            return
        
        if self._media_client.time_stamp_a / (self._media_client.fps_a/1) > self._media_client.time_stamp_v / self._media_client.fps_v + 0.01:
            return

        frame = self._media_client.get_next_frame(type = 2)
        if frame is not None:
            self.stream.write(frame)
            self._media_client.time_stamp_a += 1



    def handle_setup(self):
        self._media_client.start_rtsp_connection()
        self._media_client.send_setup_command()
        self.positionSlider.setRange(0, 10)
        #self.positionSlider.valueChanged.connect(self.valuechange)
        '''
        self.positionSlider.setRange(0, duration)
        self.positionSlider.setTickInterval(1/fps)
        '''
        #self.positionSlider.setPageStep(2)
        

        self.setup_button.setEnabled(False)
        self.play_button.setEnabled(True)
        self.tear_button.setEnabled(True)
        self._update_image_timer.start(1000//self._media_client.fps_v)
        self._update_audio_timer.start(1000//self._media_client.fps_a)
        self.py_audio = pyaudio.PyAudio()
        self.stream = self.py_audio.open(format = self._media_client.samplewidth_a,
                       channels = self._media_client.channels_a,
                       rate = self._media_client.fps_a,
                       output=True)

    def handle_play(self):
        if self.state == 'pause':
            self._media_client.send_play_command()
            self.state = 'play'
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        elif self.state == 'play':
            self._media_client.send_pause_command()
            self.state = 'pause'
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def handle_teardown(self):
        self._media_client.send_teardown_command()
        self.setup_button.setEnabled(True)
        self.play_button.setEnabled(False)
        # self.pause_button.setEnabled(False)
        exit(0)

    def positionChanged(self, position):
        self.positionSlider.setValue(position)
    '''
    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)
    '''
    
    def valuechange(self, position):
        position = self.positionSlider.value()
        print(position)

    def setPosition(self, position):
        print(position)
        self.mediaPlayer.setPosition(position)

    def handle_error(self):
        self.play_button.setEnabled(False)
        # self.pause_button.setEnabled(False)
        self.tear_button.setEnabled(False)
        # self.error_label.setText(f"Error: {self._media_player.errorString()}")
