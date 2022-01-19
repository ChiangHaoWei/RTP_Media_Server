from typing import Tuple
import cv2

def get_info(path:str) -> Tuple[int, int]:
    cap = cv2.VideoCapture(path)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    return (0, frame_count)


class VideoStream:
  EOF = b'\xff\xd9'

  def __init__(self, path:str) -> None:
    self.path = path
    self.cap = cv2.VideoCapture(path)
    self.fps = self.cap.get(cv2.CAP_PROP_FPS)
    self.frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

  def get_payload(self, timestamp:int) -> bytes:
    self.cap.set(cv2.CAP_PROP_POS_FRAMES, timestamp)
    ret, frame = self.cap.read()
    if not ret:
        print("frame read failed")
        break

    return bytes(frame)+EOF

  def close(self):
    self.cap.release()
  
