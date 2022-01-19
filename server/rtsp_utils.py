from ctypes import Union
from urllib.parse import urlparse
import datetime
from typing import Dict, List

from client.video_stream import get_info

def rtsp_header_parser(request:str) -> Dict[str, str]:
  lines = request.strip().split('\n')
  header = dict()

  first_line:List[str] = lines[0].strip().split(' ')
  header["method"] = first_line[0].strip().upper()
  header["url"] = first_line[1].strip()
  header["version"] = first_line[2].strip()
  header["path"] = urlparse(first_line[1].strip()).path
  for i in range(1, len(lines)):
    line = lines[i].strip().split(':')
    header[line[0].strip()] = line[1].strip()
  return header

def bad_response(version:str="RTSP/1.0", code="400 Bad Request") -> bytes:
  return rtsp_response_generator({"version":version}, code)

def rtsp_response_generator(header:Dict[str, str], code="200 OK") -> bytes:
  first_line = f"{header['version']} {code}\r\n"
  response = ''
  for key in header:
    if key=='version':
      continue
    response += f"{key}: {header[key]}\r\n"
  response+=f"Date: {str(datetime.datetime.now())}\r\n"
  return (first_line+response).encode('utf-8')

def sdp_generator(path:str):
  start_time, end_time = get_info(path)
  sdp = "m=video 0 RTP/AVP 96\r\n" \
        "a=control:streamid=0\r\n" \
        f"a=range:npt={start_time}-{end_time}\r\n" \
        f"a=length:npt={end_time-start_time}\r\n" \
        "a=rtpmap:96 MP4V-ES/5544\r\n" \
        "m=audio 0 RTP/AVP 97\r\n" \
        "a=control:streamid=1\r\n" \
        f"a=range:npt={start_time}-{end_time}\r\n" \
        f"a=length:npt={end_time-start_time}\r\n" \
        "a=rtpmap:97 mpeg4-generic/32000/2"
  
  return sdp.encode('utf-8')


def variable_parser(line:str):
  vars:Dict[str, Union[str, int, float]] = dict()

  if ";" in line:
    for pair in line.strip().split("="):
      key = pair[0]
      try:
        if "." in pair[1]:
          value = float(pair[1])
        else:
          value = int(pair[1])
      except ValueError as e:
        value = pair[1]
      except:
        raise
  else:
    pair = line.strip().split("=")
    key = pair[0]
    try:
      if "." in pair[1]:
        value = float(pair[1])
      else:
        value = int(pair[1])
    except ValueError as e:
      value = pair[1]
    except:
      raise
  vars[key] = value
  return vars
  
