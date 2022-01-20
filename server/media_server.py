import socket
from uuid import uuid4
import threading
import time
from client.audio_stream import AudioStream
from client.video_stream import VideoStream, get_info

from server.rtphost import RTPHost
from server.rtsp_utils import rtsp_header_parser, rtsp_response_generator, bad_response, sdp_generator, variable_parser
from typing import Any, Dict, List, Tuple

class MediaServer:
  TIME_OUT = 30
  def __init__(self, address:str, port:int) -> None:
    self.addr = address
    self.port = port
    self.available_port = [1000, 1100, 1200, 1300, 1400, 1500, 1600]
    self.clients:Dict[str, RTPHost] = dict()
    self.buffer:List[threading.Thread] = list()
  
  def init(self):
    self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    self.rtsp_socket.settimeout(5)
    self.rtsp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.rtsp_socket.bind((self.addr, self.port))
    self.rtsp_socket.listen(5)
  
  def handle_on_client(self, client:socket.socket, addr:Tuple[str, int]):
    
    while True:
      try:
        message = client.recv(4096).decode('utf-8')
        header = rtsp_header_parser(message)
        print(f"Receive request from client: {addr}")
        print(message)
      except socket.timeout:
        continue
      try:
        # SETUP
        if header["method"] == "SETUP":
          if len(self.available_port) == 0:
            response = bad_response(code="503 Service Unavailable")
          else:
            # session if
            session = str(uuid4()) if "Session" not in header else header["Session"]
            # client info
            client_info = RTPHost(addr[0], addr[1], session)
            client_info.path = header["path"]
            try:
              client_info.play_place, client_info.end_place, _, _ = get_info(header["path"])
            except:
              response = bad_response(code="404 Not Found")
            else:
              # transport
              trans_info = header["Transport"].split(";")
              for value in trans_info:
                if value.startswith("RTP/AVP/TCP"):
                  client_info.type = "TCP"
                elif value.startswith("client_port"):
                  client_info.client_port = int(value[value.find("=")+1:value.find("-")])
                  assert client_info.client_port % 2 == 0
                  client_info.server_port = self.available_port.pop()
              # RTP stream
              if "streamid" in header["param"] and header["param"]["streamid"][0] == "1":
                client_info.stream = AudioStream(header["path"])
              else:
                client_info.stream = VideoStream(header["path"])
              # store client information
              self.clients[session] = client_info
              # response
              res_header = {
                "version": header["version"],
                "CSeq": header["CSeq"],
                "Transport": header["Transport"]+f";server_port:{client_info.server_port}-{client_info.server_port+1}",
                "Session": client_info.session
              }
              response = rtsp_response_generator(res_header)
        elif header["method"] == "DESCRIBE":
          try:
            sdp_info = sdp_generator(header["path"])
          except:
            response = bad_response(code="404 Not Found")
          else:
            res_header = {
              "version": header["version"],
              "CSeq": header["CSeq"],
              "Content-Base": header["url"],
              "Content-Type": "application/sdp",
              "Content-Length": str(len(sdp_info))
            }
            if "Session" in header:
              self.clients[header["Session"]].updata_time()
            response = rtsp_response_generator(res_header) + sdp_info
        elif header["method"] == "PLAY":
          if ("Session" not in header) or (header["Session"] not in self.clients):
            print(f"Client {addr} must send SETUP request before PLAY")
            response = bad_response(code="454 Session Not Found")
          else:
            session = header["Session"]
            # get start time and end time
            if "Range" in header:
              vars = variable_parser(header["Range"])
              if "npt" in vars:
                se = vars["npt"].split("-")
                self.clients[session].play_place = int(se[0])
                try:
                  self.clients[session].end_place = int(se[1])
                except ValueError:
                  pass
                except:
                  raise
            self.clients[session].play()
            res_header = {
              "version":header["version"],
              "CSeq":header["CSeq"],
              "Session":session,
              "RTP-Info":f"url={header['url']};seq={self.clients[session].seq_num};rtptime={self.clients[session].play_place}"
            }
            self.clients[session].updata_time()
            response = rtsp_response_generator(res_header)
        elif header["method"] == "PAUSE":
          if ("Session" not in header) or (header["Session"] not in self.clients):
            print(f"Client {addr} must send SETUP request before PLAY")
            response = bad_response(code="454 Session Not Found")
          else:
            session = header["Session"]
            self.clients[session].pause()
            res_header = {
              "version": header["version"],
              "CSeq": header["CSeq"],
              "Session": session
            }
            self.clients[session].updata_time()
            response = rtsp_response_generator(res_header)
        elif header["method"] == "TEARDOWN":
          if ("Session" not in header) or (header["Session"] not in self.clients):
            print(f"Client {addr} must send SETUP request before PLAY")
            response = bad_response(code="454 Session Not Found")
          else:
            session = header["Session"]
            self.clients[session].stop()
            res_header = {
              "version": header["version"],
              "CSeq": header["CSeq"]
            }
            self.available_port.append(self.clients[session].server_port)
            del self.clients[session]
            
            response = rtsp_response_generator(res_header)
            client.send(response)
            break
        else:
          response = bad_response(code="405 Method Not Allowed")
      except:
        response = bad_response()
      # send response to client
      print("Response")
      print(response.decode("utf-8"))
      client.send(response)
    print(f"Client {addr} disconnect")
    client.close()  

  def check_timeout(self):
    timeouts = list()
    for key, host in self.clients.items():
      if time.time()-host.time > self.TIME_OUT:
        print(f"Client ({host.addr}, {host.port}) with session id {host.session} timeout")
        timeouts.append(key)
    for key in timeouts:
      self.clients[key].stop()
      self.available_port.append(self.clients[key].server_port)
      del self.clients[key]
  def rtsp_server(self):
    print(f"RTSP server is ready to serve at ({self.addr}, {self.port})")
    while True:
      try:
        client, addr = self.rtsp_socket.accept()
        print(f"Client {addr} is connected!")
      except socket.timeout:
        pass
      else:
        # TODO
        if len(self.buffer) >= 5:
          for t in self.buffer:
            t.join()
        self.buffer.append(threading.Thread(target=self.handle_on_client, args=(client, addr)))
        self.buffer[-1].setDaemon(True)
        self.buffer[-1].start()
        
      self.check_timeout()

if __name__ == "__main__":
  HOST, PORT = "127.0.0.1", 1234
  media_server = MediaServer(HOST, PORT)
  media_server.init()
  media_server.rtsp_server()          