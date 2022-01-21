
import threading
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
from PIL import Image
import cv2
import time

from client.client import Client
#from utils.video_stream import VideoStream

import pyaudio
import os


class ClientWindow(QMainWindow):
    _update_image_signal = pyqtSignal()
    _update_audio_signal = pyqtSignal()
    _run_loading_signal = pyqtSignal()

    def __init__(
            self,
            file_name: str,
            host_address: str,
            host_port: int,
            rtp_port_v: int,
            rtp_port_a: int,
            localhost:str,
            parent=None):
        super(ClientWindow, self).__init__(parent)

        self.loading_list = []
        for i in range(61):
            image = Image.open(os.path.join("loading_image",f'frame-{i+1}.png'))
            self.loading_list.append(image)
        self.current_loading = 0

        self.nframe = 0
        self.video_player = QLabel(alignment=Qt.AlignCenter)

        self.current_label = QLabel('00:00', self)
        self.current_label.setAlignment(Qt.AlignCenter)
        self.current_label.setMinimumWidth(5)

        self.play_button = QPushButton()
        self.state = 'init'


        self.positionSlider = QSlider(Qt.Horizontal, self)
        self.positionSlider.setRange(0, 0)
        #self.positionSlider.sliderMoved.connect(self.setPosition)
        self.positionSlider.valueChanged.connect(self.valuechange)
        
        self.end_label = QLabel('00:00', self)
        self.end_label.setAlignment(Qt.AlignCenter)
        self.end_label.setMinimumWidth(5)

        self.setup_button = QPushButton()
        self.tear_button = QPushButton()
        self.error_label = QLabel()

        

        self._media_client = Client(file_name, host_address, host_port, rtp_port_v, rtp_port_a, localhost)
        self._update_image_signal.connect(self.update_image)
        self._update_image_timer = QTimer()
        self._update_image_timer.timeout.connect(self._update_image_signal.emit)

        # self._update_audio_signal.connect(self.update_audio)
        # self._update_audio_timer = QTimer()
        # self._update_audio_timer.timeout.connect(self._update_audio_signal.emit)

        self._run_loading_signal.connect(self.run_loading)
        self._run_loading_timer = QTimer()
        self._run_loading_timer.timeout.connect(self._run_loading_signal.emit)
        self._run_loading_timer.setInterval(1000//30)

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        videoWidget = QVideoWidget()

        self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        # self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handle_error)

        self.audio_job = threading.Thread(target=self.update_audio)
        self.audio_job.setDaemon(True)
        self.is_stop = False
        self.audio_stream_playing = False
        self.start_frame = -1
        self.last_start_time = time.time()
        self.play_time = 0

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
        control_layout.addWidget(self.current_label)
        control_layout.addWidget(self.positionSlider)
        control_layout.addWidget(self.end_label)
        control_layout.addWidget(self.setup_button)
        control_layout.addWidget(self.tear_button)

        layout = QVBoxLayout()
        layout.addWidget(self.video_player)
        layout.addLayout(control_layout)
        layout.addWidget(self.error_label)

        central_widget.setLayout(layout)

    def get_interval(self):
        cur_time = time.time() - self.last_start_time + self.play_time
        video_time = self._media_client.time_stamp_v/self._media_client.fps_v
        if video_time > cur_time:
            return 1000//self._media_client.fps_v + (video_time-cur_time)*1000
        else:
            return max((1000//self._media_client.fps_v - (cur_time-video_time)*1000), 1)

    def update_image(self):
        if not self._media_client.is_playing:
            return

        # if self._media_client.time_stamp_v / self._media_client.fps_v > self._media_client.time_stamp_a / (self._media_client.fps_a/1) + 0.01:
        #     return
        self._update_image_timer.stop()
        frame = self._media_client.get_next_frame(type = 1)
        #frame = self._media_client.get_next_frame(type=2)

        #frame , timestamp= self._media_client.get_next_frame()
        #self.positionSlider.setValue(timestamp)
        if frame is not None:
            print("received frame!")
            decode_frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            image = Image.fromarray(cv2.cvtColor(decode_frame,cv2.COLOR_BGR2RGB))
            pix = QPixmap.fromImage(ImageQt(image).copy())
            self.video_player.setPixmap(pix)
            current_time = self._media_client.time_stamp_v//self._media_client.fps_v
            current_sec = current_time % 60
            current_min = current_time // 60
            self.current_label.setText(f'{current_min:02}:{current_sec:02}')
            self.positionSlider.setValue(self._media_client.time_stamp_v)
            self._media_client.time_stamp_v += 1
        self._update_image_timer.setInterval(self.get_interval())
        self._update_image_timer.start()

    def update_audio(self):
        while not self.is_stop:
            if len(self._media_client.frame_buffer_a) > 0 and self.audio_stream_playing:
                frame = self._media_client.get_next_frame(type=2)
                if frame is not None:
                    self._media_client.stream_player.write(frame)
                    self._media_client.time_stamp_a += 1
            time.sleep(0.0001)
        print("job end")
        # frame = self._media_client.get_next_frame(type = 2)
        # if frame is not None:
        #     print("audio frame", frame)
        #     self.stream.write(frame)
        #     self._media_client.time_stamp_a += 1
    def handle_setup(self):
        self._media_client.start_rtsp_connection()
        self._media_client.send_setup_command()
        self.positionSlider.setRange(0, self._media_client.length_v)
        time_length_in_sec = self._media_client.length_v / self._media_client.fps_v
        minutes = int(time_length_in_sec // 60)
        sec = int((time_length_in_sec % 60))
        self.end_label.setText(f'{minutes:02}:{sec:02}')
        '''
        self.positionSlider.setRange(0, duration)
        self.positionSlider.setTickInterval(1/fps)
        '''
        #self.positionSlider.setPageStep(2)
        self.resize(self._media_client.width_v, self._media_client.height_v)
        self.setup_button.setEnabled(False)
        self.play_button.setEnabled(True)
        self.tear_button.setEnabled(True)
    
    def run_loading(self):
        # self._run_loading_timer.start(1000//self._media_client.fps_v)
        
        if len(self._media_client.frame_buffer_v) > 120 or len(self._media_client.frame_buffer_a) > 120:
            if not self.audio_job.is_alive() and self.state=='init':
                self.audio_job.start()
            else:
                self._media_client.stream_player.start_stream()
            self.audio_stream_playing = True
            self.last_start_time = time.time()
            self._run_loading_timer.stop()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self._update_image_timer.start(1000//self._media_client.fps_v)
            self.play_button.setEnabled(True)
            self.state = 'play'
            return
        else:
            print("loading....❤❤❤❤🤣")
        frame = self.loading_list[self.current_loading]
        pix = QPixmap.fromImage(ImageQt(frame).copy())
        self.video_player.setPixmap(pix)
        self.current_loading += 1
        if self.current_loading >= 61:
            self.current_loading -= 61
        

    def handle_blocking(self):
        self.play_button.setEnabled(False)
        print("loading....❤❤❤❤🤣")
        while len(self._media_client.frame_buffer_v) < 120 or len(self._media_client.frame_buffer_a) < 120:
            frame = self.loading_list[self.current_loading]
            pix = QPixmap.fromImage(ImageQt(frame).copy())
            self.video_player.setPixmap(pix)
            self.current_loading += 1
            if self.current_loading >= 61:
                self.current_loading -= 61
            time.sleep(1/60)
        if not self.audio_job.is_alive() and self.state=='init':
            self.audio_job.start()
        
        
    def handle_play(self):
        if self.state == "init":
            
            self._run_loading_timer.start()
            self._media_client.send_play_command()
            # self.handle_blocking()
        elif self.state == 'pause':
            # self.handle_blocking()
            self._run_loading_timer.start()
            self._media_client.send_play_command()
            # self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            # self.play_button.setEnabled(True)
            # self._update_image_timer.start(1000//self._media_client.fps_v)
            # self._media_client.stream_player.start_stream()
            self.last_start_time = time.time()
            self.state = 'play'
        elif self.state == 'play':
            self.play_time += time.time() - self.last_start_time
            self.audio_stream_playing = False
            self._media_client.send_pause_command()
            self._update_image_timer.stop()
            self._media_client.stream_player.stop_stream()
            self.state = 'pause'
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def handle_teardown(self):
        self._media_client.send_teardown_command()
        self.setup_button.setEnabled(True)
        self.play_button.setEnabled(False)
        self.is_stop = True
        self.audio_job.join()
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
