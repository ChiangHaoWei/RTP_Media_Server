class AudioStream:
  def __init__(self, path:str) -> None:
    self.path = path
  def get_payload(self, timestamp:int) -> bytes:
    return "123".encode()