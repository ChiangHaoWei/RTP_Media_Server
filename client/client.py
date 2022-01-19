from io import BytesIO
import socket
from threading import Thread
import time
import heapq
from typing import List
from PIL import Image
from client.utils import rtsp_request_generator, rtp_response_parser, rtsp_reponse_parser

class Client:
    localhost = '127.0.0.1'
    FRAME_SIZE = 1024
    RTSP_TIMEOUT = 100/1000
    RTP_TIMEOUT = 5/1000
    EOF = b'\xff\xd9'
    def __init__(self, file_path, host_addr, host_port, rtp_port):
        self.is_rtsp_connected = False
        self.is_playing = False
        self.file_path = file_path
        self.host_addr = host_port
        self.host_port = host_addr
        self.rtp_port = rtp_port
        self.seq_num = 0
        self.frame_buffer_v = []
        heapq.heapify(self.frame_buffer_v)
        self.frame_buffer_a = []
        heapq.heapify(self.frame_buffer_a)

        self.session_id_v:str=None
        self.session_id_a:str=None
        self.frame_buffer_v:List[bytes] = []
        heapq.heapify(self.frame_buffer_v)
        self._frame_buffer_a:List[bytes] = []
        heapq.heapify(self._frame_buffer_a)

    # setup
    def start_rtsp_connection(self):
        if self.is_rtsp_connected:
            return
        # create rtsp socket
        self._rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect socket to address port
        self._rtsp_socket.connect((self.host_addr, self.host_port))
        self._rtsp_socket.settimeout(self.RTSP_TIMEOUT)
        # timeout
        # self.rtsp_socket.settimeout(rtsp_timeout)
        self.is_rtsp_connected = True

    def _receive_rtp_packet(self,type, size = FRAME_SIZE):
        recv_bstr = bytes() # bstr
        # receive until EOF -> a full packet
        while 1:
            try:
                if type == 1:
                    temp = self._rtp_socket_v.recv(size)
                elif type == 2:
                    temp = self._rtp_socket_a.recv(size)
                if temp.endswith(self.EOF):
                    break
            except socket.timeout:
                continue
        # convert response string to packet
        # return RTPPacket.from_packet(recv_bstr)
        return rtp_response_parser(recv_bstr)

    # receive rtp packet continuously
    # 2 rtp packet, 1 video, 1 audio
    def _receive_video(self):
        # video
        self._rtp_socket_v = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rtp_socket_v.bind((self.localhost, self.rtp_port_v))
        self._rtp_socket_v.settimeout(self.RTP_TIMEOUT)
        # audio
        self._rtp_socket_a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rtp_socket_a.bind((self.localhost, self.rtp_port_a))
        self._rtp_socket_a.settimeout(self.RTP_TIMEOUT)
        # timeout
        # self._rtp_socket.settimeout()

        # receive frame, add to frame buffer, a min heap
        # format: (time_stamp, frame)
        while True:
            if not self.is_playing:
                time.sleep(1)

            # video
            packet = self._receive_rtp_packet(type=1)
            frame = Image.open(BytesIO(packet['payload']))
            # heapq.heappush(self.frame_buffer_v, (packet['seq_num'], frame))
            heapq.heappush(self.frame_buffer_v, (packet['time_stamp'], frame))

            # audio
            packet = self._receive_rtp_packet(type=2)
            # heapq.heappush(self.frame_buffer_a, (packet['seq_num'], packet['payload']))
            heapq.heappush(self.frame_buffer_a, (packet['time_stamp'], packet['payload']))

    # create a parallel thread for _receive_video 
    def _start_receive_video_thread(self):
        self.receive_video_thread = Thread(target = self._receive_video)
        self.receive_video_thread.setDaemon(True) # auto terminated with process
        self.receive_video_thread.start()

    # send RTSP request to server
    def _send_rtsp_request(self, command, _type, start=0):
        # return if not connected
        if not self.is_rtsp_connected:
            # raise Exception("rtsp connection not created")
            print("rtsp connection not created")
            return False
        request_dict = dict()
        request_dict['command'] = command
        if _type == 1:
            request_dict['file_path'] = self.file_path_v
            request_dict['CSeq'] = self.seq_num_v
            client_port = self.rtp_port_v
            if self.session_id_v:
                request_dict['Session'] = self.session_id_v
            self.seq_num_v += 1
        elif _type == 2:
            request_dict['file_path'] = self.file_path_a
            request_dict['CSeq'] = self.seq_num_a
            request_dict['client_port'] = self.rtp_port_a
            if self.session_id_a:
                request_dict['Session'] = self.session_id_a
            self.seq_num_a += 1
        setup_type = None
        if command == 'SETUP':
            request_dict['Transport'] = f'RTP/UDP;unicast;client_port={client_port}'
            setup_type = _type
        elif command == 'PLAY' and start:
            request_dict['Range'] = f'npt={start}-'
        request_bstr = rtsp_request_generator(request_dict, setup_type)
        self._rtsp_socket.send(request_bstr)
        return self._get_response()

    def get_next_frame(self, type):
        # self._frame_num += 1
        # if min frame time < playing time -> pop
        # pop the payload of the element with the smallest time_stamp

        if type == 1:
            if not self._frame_buffer_v:
                return None
            # omit until time reached
            while self._frame_buffer_v[0][0] < self.time_stamp:
                heapq.heappop(self.frame_buffer_v)[1]
            # give the frame of desired time
            output = heapq.heappop(self.frame_buffer_v)[1]
            self.time_stamp = output[0]
            return output[1], self.time_stamp
        elif type == 2:
            if not self._frame_buffer_a:
                return None
            while self._frame_buffer_a[0][0] < self.time_stamp:
                heapq.heappop(self.frame_buffer_a)[1]
            output = heapq.heappop(self.frame_buffer_a)[1]
            self.time_stamp = output[0]
            return output[1], self.time_stamp
    
    # <commands>
    # def send_command(self, command):
    #     # video
    #     res = self._send_rtsp_request("SETUP", type=1)
    #     if not res or res['code'] != '200':
    #         return
    #     if command == 'PLAY':
    #         self.session_id_v = res['session_id']

    #     # audio
    #     res = self._send_rtsp_request("SETUP", type=2)
    #     if not res or res['code'] != '200':
    #         return
    #     if command == 'PLAY':
    #         self.session_id_a = res['session_id']

    #     if command == 'SETUP':
    #         self._start_receive_video_thread()
    #     elif command == 'PLAY':
    #         self.is_playing = True
    #     elif command == 'PAUSE':
    #         self.is_playing = False
    #     elif command == 'TEARDOWN':
    #         self._rtsp_connection.close()
    #         self.is_playing = False
    #         self.is_rtsp_connected = False


    def send_setup_command(self):
        res = self._send_rtsp_request("SETUP", type=1)
        if not res or res['code'] != '200':
            return
        self.session_id_v = res['session_id']

        res = self._send_rtsp_request("SETUP", type=2)
        if not res or res['code'] != '200':
            return
        self.session_id_a = res['session_id']

        self._start_receive_video_thread()

    def send_describe_command(self):
        res = self._send_rtsp_request("DESBRIBE", type=1)
        if not res or res['code'] != '200':
            return

        res = self._send_rtsp_request("DESBRIBE", type=2)
        if not res or res['code'] != '200':
            return
        # format: a=length:npt=7.741000
        self.video_length = res['a=length'].split('=')[1]
        return self.video_length

    def send_play_command(self, start=None):
        # alter time -> start = that time
        if start != None:
            self.frame_buffer_v = []
            heapq.heapify(self.frame_buffer_v)
            self.frame_buffer_a = []
            heapq.heapify(self.frame_buffer_a)
        # no start passed -> normal play request, start at where it's left off
        res = self._send_rtsp_request("PLAY", type=1, start=start)
        if not res or res['code'] != '200':
            return
        self.session_id_v = res['session_id']

        res = self._send_rtsp_request("PLAY", type=2, start=start)
        if not res or res['code'] != '200':
            return

        self.is_playing = True

    def send_pause_command(self):
        res = self._send_rtsp_request("PAUSE", type=1)
        if not res or res['code'] != '200':
            return

        res = self._send_rtsp_request("PAUSE", type=2)
        if not res or res['code'] != '200':
            return

        self.is_playing = False

    def send_teardown_command(self):
        res = self._send_rtsp_request("TEARDOWN", type=1)
        if not res or res['code'] != '200':
            return

        res = self._send_rtsp_request("TEARDOWN", type=2)
        if not res or res['code'] != '200':
            return

        self._rtsp_connection.close()
        self.is_playing = False
        self.is_rtsp_connected = False
    # </commands>

    def _get_response(self, size = FRAME_SIZE):
        while True:
            try:
                recv = self._rtsp_socket.recv(size)
                break
            except socket.timeout:
                continue
        response = rtsp_reponse_parser()
        return response