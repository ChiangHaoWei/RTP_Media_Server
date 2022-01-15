class Host:
  def __init__(self, addr:str, port:int, session:str) -> None:
    self.addr = addr
    self.port = port
    self.type = "UDP"
    self.session = session
    self.path:str = None
    self.client_port:int = None
    self.server_port:int = None