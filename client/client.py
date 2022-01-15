import socket
from threading import Thread
from server.rtsp_packet import RTSPPacket 
from PIL import Image

class Client:
    # rtsp_timeout
    localhost = '127.0.0.1'
    def __init__(self, file, host_addr, host_port, rtp_port):
        self.is_rtsp_connected = False
        self.is_playing = False
        self.file = file
        self.host_addr = host_port
        self.host_port = host_addr
        self.rtp_port = rtp_port
        self.seq_num = 0
        self._frame_buffer = []
    # setup
    def start_rtsp_connection(self):
        if self.is_rtsp_connected:
            return
        # create rtsp socket
        self._rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect socket to address port
        self._rtsp_socket.connect((self.host_addr, self.host_port))
        # timeout
        # self.rtsp_socket.settimeout(rtsp_timeout)
        self.is_rtsp_connected = True

    def _receive_rtp_packet(self):
        recv_bstr = bytes() # bstr
        while 1:
            temp = self._rtp_socket.recv(size)
            recv_bstr += temp
            if temp == b'\xff\xd9': break # EOF
        # convert response string to packet
        return RTSPPacket.from_packet(recv_bstr)

    # receive rtp packet continuously
    def _receive_video(self):
        self._rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rtp_socket.bind((self.localhost, self.rtp_port))
        # timeout
        # self._rtp_socket.settimeout()

        # receive frame, add to frame buffer
        while 1:
            packet = self._receive_rtp_packet()
            frame = Image.open(BytesIO(packet.payload))
            self.frame_buffer.append(frame)

    # create a parallel thread for _receive_video 
    def _start_receive_video_thread(self):
        self.receive_video_thread = Thread(target = _receive_video)
        self.receive_video_thread.setDaemon(True) # auto terminated with process
        self.receive_video_thread.start()

    # send RTSP request to server
    def _send_command(self, command):
        # return if not connected
        if not self.is_rtsp_connected:
            # raise Exception("rtsp connection not created")
            print("rtsp connection not created")
            return False
        # create request string
        command_request = RTSPPacket(
            command,
            self.file,
            self.seq_num,
            self.rtp_port
        ).to_request()
        # send request string to server
        self._rtsp_socket.send(command_request)
        self.seq_num += 1
        # get response?

        return True

    def get_next_frame(self):
        if not self._frame_buffer:
            return None
        self._frame_num += 1
        return self._frame_buffer.pop(0)

    # <commands>
    def send_setup_command(self):
        # send to server
        succ = self._send_command(RTSPPacket.SETUP)
        if not succ: return
        # session id ??
        self._start_receive_video_thread()

    def send_play_command(self):
        succ = self._send_command(RTSPPacket.PLAY)
        if not succ: return
        self.is_playing = True

    def send_pause_command(self):
        succ = self._send_command(RTSPPacket.PAUSE)
        self.is_playing = False

    def send_teardown_command(self):
        succ = self._send_command(RTSPPacket.TEARDOWN)
        self._rtsp_connection.close()
        self.is_playing = False
        self.is_rtsp_connected = False

    # </commands>