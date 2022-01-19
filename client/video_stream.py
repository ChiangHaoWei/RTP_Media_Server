from typing import Tuple
import cv2
import wave

def get_info(path:str) -> Tuple[int, int, int, dict]:
    cap = cv2.VideoCapture(path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    wave_file = wave.open(f"{path[:path.find('.mp4')]}.wav", 'rb')

    audio_info = {"samplewidth": int(wave_file.getsampwidth()), 
    "channels": int(wave_file.getnchannels()),
    "fps": int(wave_file.getframerate())
    }
    print("video fps", video_fps)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    return (0, frame_count, video_fps, audio_info)


class VideoStream:
  EOF = b'\xff\xd9'

  def __init__(self, path:str) -> None:
    self.path = path
    self.cap = cv2.VideoCapture(path)
    self.fps = self.cap.get(cv2.CAP_PROP_FPS)
    self.frame_count = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)

  def get_payload(self, timestamp:int) -> bytes:
    self.cap.set(cv2.CAP_PROP_POS_FRAMES, timestamp)
    ret, frame = self.cap.read()
    if not ret:
        print("frame read failed")
    # print(f"size of video frame: {len(bytes(frame))}")
    # ret,  jpg_frame = cv2.imencode('.jpg', frame)
    # if not ret:
    #     print("frame read failed")
    return bytes(frame)+self.EOF

  def close(self):
    self.cap.release()
  
