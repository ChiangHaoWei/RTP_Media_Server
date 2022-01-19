from ctypes import Union
import threading
import time

from client.audio_stream import AudioStream
from client.video_stream import VideoStream

class RTPHost:
  def __init__(self, addr:str, port:int, session:str) -> None:
    self.addr = addr
    self.port = port
    self.type = "UDP"
    self.session = session
    self.path:str = None
    self.client_port:int = None
    self.server_port:int = None
    self.play_place = 0
    self.end_place = -1
    self.playing = False
    self.job:threading.Thread = None
    self.time:float = time.time()
    self.stream:Union[AudioStream, VideoStream]
  def updata_time(self):
    self.time = time.time()
  def play(self):
    self.playing = True
    # TODO
  def pause(self):
    self.playing = False
    # TODO
  def stop(self):
    self.playing = False
    # TODO