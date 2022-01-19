import threading
import time
import socket

from client.audio_stream import AudioStream
from client.video_stream import VideoStream
from server.rtp_utils import rtp_packet_generator

from typing import Union

class RTPHost:
  SERVER = "127.0.0.1"
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
    self.stream:Union[AudioStream, VideoStream] = None
    self.seq_num = 0
  
  def send_rtp_packet(self):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((self.SERVER, self.server_port))
    print(f"RTP server start at port {self.server_port}")
    print(f"Send RTP packet to client at ({self.addr}, {self.client_port})")
    assert self.end_place >= self.play_place
    while self.playing and (self.play_place < self.end_place):
      print(f"Send packet #{self.seq_num} with timestamp={self.play_place}")
      payload = self.stream.get_payload(self.play_place)
      packet = rtp_packet_generator(self.seq_num, self.play_place, payload)
      self.play_place += 1
      if self.seq_num >= 2**16:
        self.seq_num = 0
      else:
        self.seq_num += 1
      assert packet.find(b'\xff\xd9') != -1, "not end with EOF"
      print(f"Packet Size: {len(packet)}")
      s.sendto(packet, (self.addr, self.client_port))
    self.playing = False
    s.close()
  def play(self):
    if not self.playing:
      self.playing = True
      self.job = threading.Thread(target=self.send_rtp_packet)
      self.job.setDaemon(True)
      self.job.start()
  def pause(self):
    if self.playing:
      self.playing = False
      self.job.join()
  def stop(self):
    if self.playing:
      self.playing = False
      self.job.join()
  def updata_time(self):
    self.time = time.time()