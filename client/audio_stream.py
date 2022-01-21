import wave
import pyaudio

class AudioStream:

  def __init__(self, path:str) -> None:
    self.path = path
    file_name = path[:path.find(".mp4")]
    wave_file = wave.open(f'{file_name}.wav', 'rb')
    self.wave_file = wave_file

    self.samplewidth = wave_file.getsampwidth()
    self.channels = wave_file.getnchannels()
    self.fps = wave_file.getframerate()
    self.cur_timestamp = 0

  def get_payload(self, timestamp:int) -> bytes:
    if timestamp!=self.cur_timestamp:
      self.cur_timestamp = timestamp
      self.wave_file.setpos(timestamp*4410)
    self.cur_timestamp += 1
    frame = self.wave_file.readframes(4410)
    print("audio frame size", len(frame))
    return frame

  def close(self):
    self.wave_file.close()