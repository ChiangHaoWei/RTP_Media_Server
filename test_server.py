from server.media_server import MediaServer
import argparse
from preprocess import convert_all
parser = argparse.ArgumentParser()
parser.add_argument("-a", "--address", required=True, help="server address", type=str)
parser.add_argument("-p", "--port", required=False, default=1234, help="server port", type=int)
args = parser.parse_args()

convert_all()
HOST, PORT = args.address, int(args.port)
media_server = MediaServer(HOST, PORT)
media_server.init()
media_server.rtsp_server()