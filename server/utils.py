from urllib.parse import urlparse
import datetime
from typing import Dict, List

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

def rtsp_response_generator(header:Dict[str, str], code="200 OK")->bytes:
  first_line = f"{header['version']} {code}\r\n"
  response = ''
  for key in header:
    if key=='version':
      continue
    response += f"{key}: {header[key]}\r\n"
  response+=f"Date: {str(datetime.datetime.now())}\r\n"
  return (first_line+response).encode('utf-8')
