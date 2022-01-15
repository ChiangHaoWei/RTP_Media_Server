import socket
from uuid import uuid4

from server.host import Host
from server.utils import rtsp_header_parser, rtsp_response_generator, bad_response
from typing import Any, Dict, List, Tuple

class MediaServer:
  def __init__(self, address:str, port:int) -> None:
    self.addr = address
    self.port = port
    self.available_port = [1000, 1100, 1200, 1300]
    self.clients:Dict[str, Host] = dict()
  
  def init(self):
    self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.rtsp_socket.bind((self.addr, self.port))
    self.rtsp_socket.settimeout(5)
  
  def handle_on_client(self, client:socket.socket, addr:Tuple[str, int]):
    message = client.recv(4096).decode('utf-8')
    header = rtsp_header_parser(message)
    print(f"Receive request from client: {addr}")
    print(message)

    if header["method"] == "SETUP":
      # session if
      session = str(uuid4()) if "Session" not in header else header["Session"]
      # client info
      client_info = Host(addr[0], addr[1], session)
      client_info.path = header["path"]
      # transport
      trans_info = header["Transport"].split(";")
      for value in trans_info:
        if value.startswith("RTP/AVP/TCP"):
          client_info.type = "TCP"
        elif value.startswith("client_port"):
          client_info.client_port = int(value[value.find("=")+1:value.find("-")])
          assert client_info.client_port % 2 == 0
          client_info.server_port = self.available_port.pop()
      # store client information
      self.clients[session] = client_info
      # response
      res_header = {
        "version": header["version"],
        "CSeq": header["CSeq"],
        "Transport": header["Transport"]+f"server_port:{client_info}-{client_info+1}",
        "Session": client_info.session
      }
      response = rtsp_response_generator(res_header)
    elif header["method"] == "PLAY":
      if ("Session" not in header) or (header["Session"] not in self.clients):
        print(f"Client {addr} must send SETUP request before PLAY")
        response = bad_response()
      else:
        # TODO
        pass        


  
  def rtsp_server(self):
    while True:
      print("RTSP server is ready to serve ...")
      try:
        client, addr = self.rtsp_socket.accept()
      except socket.timeout:
        pass
      else:
        # TODO
        pass
        
          