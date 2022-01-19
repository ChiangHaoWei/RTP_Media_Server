import cv2

cap = cv2.VideoCapture(myrtmp_addr)

fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

class VideoStream:
    FRAME_HEADER_LENGTH = 5
    #DEFAULT_IMAGE_SHAPE = (380, 280)
    #VIDEO_LENGTH = 500
    #DEFAULT_FPS = 24

    # if it's present at the end of chunk,
    # it's the last chunk for current jpeg (end of frame)
    JPEG_EOF = b'\xff\xd9'

    def __init__(self, file_path: str):
        # for simplicity, mjpeg is assumed to be on working directory
        self._video_stream = cv2.VideoCapture(file_path)
        self._audio_stream = AudioSegment.from_file(file_path, "mp4")
        # frame number is zero-indexed
        # after first frame is sent, this is set to zero
        #self.current_frame_number = -1
        self.current_frame_number = 0
        
        ##
        self.fps = int(cap.get(cv2.CAP_PROP_FPS))
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        ##

    def close(self):
        self._stream.close()

    def get_next_video_frame(self) -> bytes:
        # sample video file format is as follows:
        # - 5 digit integer `frame_length` written as 5 bytes, one for each digit (ascii)
        # - `frame_length` bytes follow, which represent the frame encoded as a JPEG
        # - repeat until EOF
        try:
            #frame_length = self._stream.read(self.FRAME_HEADER_LENGTH)
            ret, frame = self._stream.read()
        except ValueError:
            raise EOFError
        #frame_length = int(frame_length.decode())
        #frame = self._stream.read(frame_length)
        self.current_frame_number += 1
        return bytes(frame)

    def get_next_audio_frame(self) -> bytes:
        # sample video file format is as follows:
        # - 5 digit integer `frame_length` written as 5 bytes, one for each digit (ascii)
        # - `frame_length` bytes follow, which represent the frame encoded as a JPEG
        # - repeat until EOF
        try:
            #frame_length = self._stream.read(self.FRAME_HEADER_LENGTH)
            ret, frame = self._stream.read()
        except ValueError:
            raise EOFError
        #frame_length = int(frame_length.decode())
        #frame = self._stream.read(frame_length)
        self.current_frame_number += 1
        return bytes(frame)