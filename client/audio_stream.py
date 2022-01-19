import wave
from pydub import AudioSegment
import pyaudio

class AudioStream:
  EOF = b'\xff\xd9'

  def __init__(self, path:str) -> None:
    self.path = path
    audio = AudioSegment.from_file(path, "mp4")
    file_name = path.strip('mp4')
    audio.export(f"{file_name}.wav", format="wav")

    wave_file = wave.open(f'{file_name}.wav', 'rb')
    self.wave_file = wave_file

    self.samplewidth = wave_file.getsampwidth()
    self.channels = wave_file.getnchannels()
    self.fps = wave_file.getframerate()

  def get_payload(self, timestamp:int) -> bytes:
    self.wave_file.setpos(timestamp)
    frame = self.wave_file.readframes(1)
    return frame + EOF

  def close(self):
    self.wave_file.close()