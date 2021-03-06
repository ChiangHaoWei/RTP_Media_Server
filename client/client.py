from io import BytesIO
import socket
from struct import pack
from threading import Thread
import time
import heapq
from typing import List
from PIL import Image
from client.utils import rtsp_request_generator, rtp_response_parser, rtsp_response_parser
import numpy as np
import cv2
import pyaudio

class Client:
    
    FRAME_SIZE = 2**16
    RTSP_TIMEOUT = 100/1000
    RTP_TIMEOUT = 5/1000
    EOF = b'\xff\xff\xd0\xff\xd0\xff'
    JPEG_START = b'\xff\xd8'
    JPEG_END = b'\xff\xd9'
    def __init__(self, file_path, host_addr, host_port, rtp_port_v, rtp_port_a, localhost='127.0.0.1'):
        self.is_rtsp_connected = False
        self.is_playing = False
        self.file_path = file_path
        self.localhost = localhost
        self.host_addr = host_addr
        self.host_port = host_port
        self.rtp_port_v = rtp_port_v
        self.rtp_port_a = rtp_port_a
        self.seq_num_v = 0
        self.seq_num_a = 0
        self.time_stamp_v = 0
        self.time_stamp_a = 0
        self.session_id_v:str = None
        self.session_id_a:str = None
        self.frame_buffer_v = []
        self.frame_buffer_a = []
        self.py_audio = pyaudio.PyAudio()

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

    def _receive_rtp_packet(self, remain, _type, size = FRAME_SIZE):
        recv_bstr = remain # bstr
        # receive until EOF -> a full packet
        temp = None
        while 1:
            try:
                if _type == 1:
                    # print(size)
                    temp = self._rtp_socket_v.recv(size)
                    # print(temp, len(temp))
                elif _type == 2:
                    temp = self._rtp_socket_a.recv(size)
                recv_bstr += temp
                index = recv_bstr.find(self.EOF)
                # print(temp)
                if index != -1:
                    # full packet received
                    if _type == 2:
                        pass
                        # print("received a full rtp packet")
                    recv_bstr, remain = recv_bstr[:index], recv_bstr[index+len(self.EOF):]
                    return rtp_response_parser(recv_bstr), remain
                
            except socket.timeout:
                continue

    def _receive_frame(self, _type):
        remain = bytes()
        packet_buffer = []
        received_one = False
        prev_frame_raw = b''
        prev_ind = -1
        # recieve packet until full frame gets, and then synthesize
        out_of_order = False
        while True:
            packet, remain = self._receive_rtp_packet(remain, _type)
            # print(f"packet\n{packet['payload']}\n")
            # print([i for i in packet['payload']])
            # push payload to min heap by packet index
            # print("payload size", len(packet['payload']))
            # get packets again if new frame
            # print("received: ", packet['ind'], packet['total'])
            if packet['ind'] != prev_ind + 1:
                # print("clear packet buffer")
                out_of_order = True
                packet_buffer = []
                prev_ind = -1
            if packet['ind'] == 0:
                out_of_order = False
                # pass
            # omit out of order packets
            if out_of_order:
                print("out of order (??? ???? ??;)???")
                if not received_one:
                    continue
            else:
                prev_ind = packet['ind']
                heapq.heappush(packet_buffer, (packet['ind'], packet['payload']))
                # last packet recieved
                # print("added: ", packet['ind'], packet['total'])
            if packet['ind'] == packet['total'] - 1:
                # synthesize all into a full frame
                # by the order of packet index
                frame_raw = bytes()
                # fill frame with previous frame if out of order
                if received_one and out_of_order:
                    # print("out of order, filled with prevoius frame")
                    frame_raw = prev_frame_raw
                else:
                    # print("receives a full frame !!!!")
                    received_one = True
                    while packet_buffer:
                        frame_raw += heapq.heappop(packet_buffer)[1] # payload
                prev_frame_raw = frame_raw
                time_stamp = packet['time_stamp']
                prev_ind = -1
                out_of_order = False
                # for video, uncompress and add to buffer
                if (_type == 1):
                    # bytes to np
                    assert frame_raw.startswith(self.JPEG_START) and frame_raw.endswith(self.JPEG_END), "Not a JPEG"
                    frame_np = np.frombuffer(frame_raw, dtype=np.uint8)
                    # cv2 uncompress
                    # frame_raw_np = cv2.imdecode(frame_np, cv2.IMREAD_COLOR)
                    # print("frame size", len(frame_raw))
                    # np to bytes
                    # frame = Image.fromarray(frame_raw_np)
                    # frame = Image.frombytes(frame_raw)
                    return time_stamp, frame_np
                # for audio, play it out
                elif (_type == 2):
                    # print(f'playing ... {len(frame_raw)}\n')
                    # self.stream_player.write(frame_raw)
                    time_stamp = packet['time_stamp']
                    return time_stamp, frame_raw
                    

    # receive rtp packet continuously
    # 2 rtp packet, 1 video, 1 audio
    def _receive(self, _type):
        # receive frame, add to frame buffer, a min heap
        # format: (time_stamp, frame)
        prev_timestamp = -1
        while True:
            if not self.is_playing:
                time.sleep(1)
            try:
                time_stamp, frame = self._receive_frame(_type)
            except OSError: # teardown
                print("stopped")
                return
            # packet, remain = self._receive_rtp_packet(remain, type=1)
            # print(frame)
            # frame = Image.open(frame)

            # if frame out of order then fill lossed frames with current frame
            # if _type == 2:
            #     print("audio timestamp", prev_timestamp, time_stamp)
            if time_stamp > prev_timestamp + 1:
                if _type == 1:
                    # print("video frame lossed")
                    for i in range(prev_timestamp + 1, time_stamp):
                        heapq.heappush(self.frame_buffer_v, (i, frame))
                elif _type == 2:
                    # print("audio frame lossed")
                    for i in range(prev_timestamp + 1, time_stamp):
                        heapq.heappush(self.frame_buffer_a, (i, frame))
            prev_timestamp = time_stamp
            
            if _type == 1:
                # continue
                # print("frame type", type(frame))
                heapq.heappush(self.frame_buffer_v, (time_stamp, frame))
            elif _type == 2:
                # audio will be played out directly
                heapq.heappush(self.frame_buffer_a, (time_stamp, frame))
                # continue

    def _receive_video(self):
        self._receive(_type=1)

    def _receive_audio(self):
        self._receive(_type=2)

    # create 2 threads, 1 video, 1 audio, for receiving frames
    def _start_receive_thread(self):
        self._rtp_socket_v = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rtp_socket_v.bind((self.localhost, self.rtp_port_v))
        self._rtp_socket_v.settimeout(self.RTP_TIMEOUT)
        self.receive_video_thread = Thread(target = self._receive_video)
        self.receive_video_thread.setDaemon(True) # auto terminated with process
        self.receive_video_thread.start()

        self._rtp_socket_a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rtp_socket_a.bind((self.localhost, self.rtp_port_a))
        self._rtp_socket_a.settimeout(self.RTP_TIMEOUT)
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
        print(f'command {command} sent')
        return self._get_response()

    def get_next_frame(self, type):
        # self._frame_num += 1
        # if min frame time < playing time -> pop
        # pop the payload of the element with the smallest time_stamp

        if type == 1:
            if not self.frame_buffer_v:
                return None
            # press play button -> don't give in until 30 frames in buffer
            # if self.is_start and len(self.frame_buffer_v) < 30:
            #     return
            self.is_start = False
            # omit until time reached
            while self.frame_buffer_v[0][0] < self.time_stamp_v:
                heapq.heappop(self.frame_buffer_v)[1]
            # give the frame of desired time
            timestamp, output = heapq.heappop(self.frame_buffer_v)
            
            # print("client video frame", output[1])
            return output
        elif type == 2:
            # audio will be played out directly
            # pass
            if not self.frame_buffer_a:
                return None
            # if self.is_start and len(self.frame_buffer_v) < 30:
            #     return
            # if self.is_start:
            #     return
            while self.frame_buffer_a[0][0] < self.time_stamp_a:
                heapq.heappop(self.frame_buffer_a)[1]
            timestamp, output = heapq.heappop(self.frame_buffer_a)
            # print("timestamp", timestamp, "????????????")
            # print("client audio frame", output[1])
            return output
    
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
        self.stream_player = self.py_audio.open(
            format = self.py_audio.get_format_from_width(self.samplewidth_a),
            channels = self.channels_a,
            rate = self.fps_a,
            output = True
        )
        res = self._send_rtsp_request("SETUP", type=1)
        if not res or res['code'] != '200':
            return
        self.session_id_v = res['Session']

        res = self._send_rtsp_request("SETUP", type=2)
        if not res or res['code'] != '200':
            return
        self.session_id_a = res['Session']

        self._start_receive_thread()

    def send_describe_command(self):
        res = self._send_rtsp_request("DESCRIBE", type=1)
        print(res)
        if not res or res['code'] != '200':
            # print(res)
            return

        res = self._send_rtsp_request("DESCRIBE", type=2)
        if not res or res['code'] != '200':
            return
        
        # video meta
        self.fps_v = round(float(res['FPS_v']))
        self.length_v = int(float(res['length_v']))
        self.height_v = int(res['height_v'])
        self.width_v = int(res['width_v'])

        # audio meta
        self.length_a = int(float(res['length_a']))
        self.samplewidth_a = int(res['Samplewidth_a'])
        self.channels_a = int(res['Channels_a'])
        self.fps_a = int(res['FPS_a'])

    def send_play_command(self, start=None):
        # alter time -> start = that time
        if start != None:
            self.frame_buffer_v = []
            self.frame_buffer_a = []
        # no start passed -> normal play request, start at where it's left off
        self.is_start = True
        res = self._send_rtsp_request("PLAY", type=1, start=start)
        # print(res)
        if not res or res['code'] != '200':
            return
        self.session_id_v = res['Session']
        if start != None:
            audio_start = int(start/self.fps_v*(self.fps_a/4410))
        else:
            audio_start = None
        res = self._send_rtsp_request("PLAY", type=2, start=audio_start)
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
        self.is_playing = False
        self.is_rtsp_connected = False
        self._rtsp_socket.close()
        self._rtp_socket_v.close()
        self._rtp_socket_a.close()
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