from server.media_server import MediaServer

HOST, PORT = "192.168.137.1", 1234
media_server = MediaServer(HOST, PORT)
media_server.init()
media_server.rtsp_server()