from PyQt5.QtWidgets import QApplication
from gui.client_gui import ClientWindow
import sys

app = QApplication(sys.argv)
client = ClientWindow("movie4.mp4", "127.0.0.1", 1234, 5000, 6000)
client.resize(400, 300)
client.show()
sys.exit(app.exec_())


