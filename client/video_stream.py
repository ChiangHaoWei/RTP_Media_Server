from typing import Tuple

def get_info(path:str) -> Tuple[int, int]:
  return (0, 100)

class VideoStream:
  def __init__(self, path:str) -> None:
    self.path = path
  def get_payload(self, timestamp:int) -> bytes:
    return "123".encode()
  
