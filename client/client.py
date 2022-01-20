from io import BytesIO
import socket
from threading import Thread
import time
import heapq
from typing import List
from PIL import Image
from client.utils import rtsp_request_generator, rtp_response_parser, rtsp_response_parser

class Client:
    localhost = '127.0.0.1'
    FRAME_SIZE = 1024
    RTSP_TIMEOUT = 100/1000
    RTP_TIMEOUT = 5/1000
    EOF = b'\xff\xd9'
    def __init__(self, file_path, host_addr, host_port, rtp_port_v, rtp_port_a):
        self.is_rtsp_connected = False
        self.is_playing = False
        self.file_path = file_path
        self.host_addr = host_addr
        self.host_port = host_port
        self.rtp_port_v = rtp_port_v
        self.rtp_port_a = rtp_port_a
        self.seq_num_v = 0
        self.seq_num_a = 0
        self.time_stamp_v = 0
        self.time_stamp_a = 0
        self.session_id_v:str=None
        self.session_id_a:str=None
        self.frame_buffer_v = heapq.heapify([])
        self.frame_buffer_a = heapq.heapify([])
        self.packet_buffer_v = heapq.heapify([])
        self.packet_buffer_a = heapq.heapify([])


    # setup
    def start_rtsp_connection(self):
        if self.is_rtsp_connected:
            return
        # create rtsp socket
        self._rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect socket to address port
        print(self.host_addr, self.host_port)
        self._rtsp_socket.connect((self.host_addr, self.host_port))
        self._rtsp_socket.settimeout(self.RTSP_TIMEOUT)
        # timeout
        # self.rtsp_socket.settimeout(rtsp_timeout)
        self.is_rtsp_connected = True

    def _receive_rtp_packet(self, remain, type, size = FRAME_SIZE):
        recv_bstr = remain # bstr
        # receive until EOF -> a full packet
        while 1:
            try:
                if type == 1:
                    temp = self._rtp_socket_v.recv(size)
                    print("temp", len(temp))
                elif type == 2:
                    temp = self._rtp_socket_a.recv(size)
                index = temp.find(self.EOF)
                print(temp)
                if index != -1:
                    # full packet received
                    print("receive a rtp packet")
                    recv_bstr += temp[:index]
                    return rtp_response_parser(recv_bstr), temp[index+len(self.EOF):]
                recv_bstr += temp
            except socket.timeout:
                continue
        # add packet into packet_buffer        

    def _receive_frame(self):
        remain = bytes()
        self.packet_buffer = heapq.heapify([])
        
        # recieve packet until full frame gets, and then synthesize
        while True:
            # video
            packet, remain = self._receive_rtp_packet(remain, type)
            # push payload to min heap by packet index
            heapq.heappush(self.packet_buffer, (packet['ind'], packet['payload']))
            # last packet recieved
            if packet['ind'] == packet['total']:
                # synthesize all into a full frame
                frame = bytes()
                # by the order of packet index
                while self.packet_buffer:
                    frame += heapq.heappop(self.packet_buffer)[1]
                # todo: cv2 imdecode
                time_stamp = packet['time_stamp']
                return time_stamp, frame

    # receive rtp packet continuously
    # 2 rtp packet, 1 video, 1 audio
    def _receive(self, type):
        # receive frame, add to frame buffer, a min heap
        # format: (time_stamp, frame)
        # remain = bytes()
        while True:
            if not self.is_playing:
                time.sleep(1)

            time_stamp, frame = self._receive_frame()
            # packet, remain = self._receive_rtp_packet(remain, type=1)
            frame = Image.open(frame)
            if type == 1:
                heapq.heappush(self.frame_buffer_v, (time_stamp, frame))
            elif type == 2:
                heapq.heappush(self.frame_buffer_a, (time_stamp, frame))

    def _receive_video(self):
        self._rtp_socket_v = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rtp_socket_v.bind((self.localhost, self.rtp_port_v))
        self._rtp_socket_v.settimeout(self.RTP_TIMEOUT)
        self._receive(self, type=1)

    def _receive_audio(self):
        self._rtp_socket_a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rtp_socket_a.bind((self.localhost, self.rtp_port_a))
        self._rtp_socket_a.settimeout(self.RTP_TIMEOUT)
        self._receive(self, type=2)

    # create 2 threads, 1 video, 1 audio, for receiving frames
    def _start_receive_thread(self):
        self.receive_video_thread = Thread(target = self._receive_video)
        self.receive_video_thread.setDaemon(True) # auto terminated with process
        self.receive_video_thread.start()

        self.receive_audio_thread = Thread(target = self._receive_audio)
        self.receive_audio_thread.setDaemon(True) # auto terminated with process
        self.receive_audio_thread.start()

    # send RTSP request to server
    def _send_rtsp_request(self, command, type, start=0):
        # return if not connected
        if not self.is_rtsp_connected:
            # raise Exception("rtsp connection not created")
            print("rtsp connection not created")
            return False
        request_dict = dict()
        request_dict['command'] = command
        if type == 1:
            request_dict['file_path'] = self.file_path
            request_dict['CSeq'] = self.seq_num_v
            client_port = self.rtp_port_v
            if self.session_id_v:
                request_dict['Session'] = self.session_id_v
            self.seq_num_v += 1
        elif type == 2:
            request_dict['file_path'] = self.file_path
            request_dict['CSeq'] = self.seq_num_a
            request_dict['client_port'] = self.rtp_port_a
            client_port = self.rtp_port_a
            if self.session_id_a:
                request_dict['Session'] = self.session_id_a
            self.seq_num_a += 1
        setup_type = None
        if command == 'SETUP':
            request_dict['Transport'] = f'RTP/UDP;unicast;client_port={client_port}-{client_port+1}'
            setup_type = type
        elif command == 'PLAY' and start:
            request_dict['Range'] = f'npt={start}-'
        request_bstr = rtsp_request_generator(self.host_addr,request_dict, setup_type)
        print(request_bstr.decode('utf-8'))
        self._rtsp_socket.send(request_bstr)
        return self._get_response()

    def get_next_frame(self, type):
        # self._frame_num += 1
        # if min frame time < playing time -> pop
        # pop the payload of the element with the smallest time_stamp

        if type == 1:
            if not self.frame_buffer_v:
                return None
            # omit until time reached
            while self.frame_buffer_v[0][0] < self.time_stamp_v:
                heapq.heappop(self.frame_buffer_v)[1]
            # give the frame of desired time
            output = heapq.heappop(self.frame_buffer_v)[1]
            self.time_stamp = output[0]
            return output[1], self.time_stamp
        elif type == 2:
            if not self.frame_buffer_a:
                return None
            while self.frame_buffer_a[0][0] < self.time_stamp_a:
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
        self.send_describe_command()
        res = self._send_rtsp_request("SETUP", type=1)
        if not res or res['code'] != '200':
            return
        self.session_id_v = res['Session']

        res = self._send_rtsp_request("SETUP", type=2)
        if not res or res['code'] != '200':
            return
        self.session_id_a = res['Session']

        self._start_receive_video_thread()

    def send_describe_command(self):
        res = self._send_rtsp_request("DESCRIBE", type=1)
        
        if not res or res['code'] != '200':
            print(res)
            return

        res = self._send_rtsp_request("DESCRIBE", type=2)
        if not res or res['code'] != '200':
            return
        
        # video meta
        print(res)
        self.fps_v = round(float(res['FPS_v']))
        
        # audio meta
        self.length_a = int(float(res['length_a']))
        self.samplewidth_a = int(res['Samplewidth_a'])
        self.channels_a = int(res['Channels_a'])
        self.fps_a = int(res['FPS_a'])

    def send_play_command(self, start=None):
        # alter time -> start = that time
        if start != None:
            self.frame_buffer_v = []
            heapq.heapify(self.frame_buffer_v)
            self.frame_buffer_a = []
            heapq.heapify(self.frame_buffer_a)
        # no start passed -> normal play request, start at where it's left off
        res = self._send_rtsp_request("PLAY", type=1, start=start)
        print(res)
        if not res or res['code'] != '200':
            return
        self.session_id_v = res['Session']

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
        response = rtsp_response_parser(recv)
        return response