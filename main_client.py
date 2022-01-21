from PyQt5.QtWidgets import QApplication
from gui.client_gui import ClientWindow
import sys
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", required=False, default="movie4.mp4", help="movie name", type=str)
parser.add_argument("-a", "--address", required=True, help="server address", type=str)
parser.add_argument("-p", "--port", required=False, default=1234, help="server port", type=int)
parser.add_argument("-l", "--localhost", required=False, default="127.0.0.1", help="localhost IP", type=str)
args = parser.parse_args()

app = QApplication(sys.argv)
client = ClientWindow(args.name, args.address, int(args.port), 5000, 6000, args.localhost)
client.resize(400, 300)
client.show()
sys.exit(app.exec_())


