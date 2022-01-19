from PyQt5.QtWidgets import QApplication
from gui.client_gui import ClientWindow
import sys

app = QApplication(sys.argv)
client = ClientWindow("movie.mp4", "127.0.0.1", 1234, 5000)
client.resize()


