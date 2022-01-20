def rtsp_request_generator(host_addr, req_dict, setup_type=None):
    version = "RTSP/1.0"
    if setup_type:
        # streamid=0 for video, 1 for audio
        req_dict['file_path'] += f"?streamid={setup_type-1}"
    req_str = f"{req_dict['command']} rtsp://{host_addr}/{req_dict['file_path']} {version}\r\n"

    for key in req_dict:
        if key in {'command', 'file_path', 'port'}:
            continue
        req_str += f"{key}: {req_dict[key]}\r\n"
    # req_str += f"Transport: RTP/UDP;unicast;client_port={client_port}\r\n"
    return req_str.encode()

def rtsp_response_parser(res_bstr):
    res_lines = res_bstr.decode().split('\r\n')
    res_code = res_lines[0].split(' ')[1]
    res_dict = dict()
    res_dict['code'] = res_code
    is_video = True
    for line in res_lines[1:]:
        # SDP line
        # is video
        if 'streamid=0' in line:
            is_video = True
            continue
        # is audio
        if 'streamid=1' in line:
            is_video = False
            continue

        if '=' in line: # SDP section
            temp = sdp_variable_parser(line)
            if not temp: 
                continue
            if is_video:
                res_dict[f'{temp[0]}_v'] = temp[1]
            else:
                res_dict[f'{temp[0]}_a'] = temp[1]
        elif ':' in line: # top section
            # not SDP line
            temp = line.split(':')
            res_dict[temp[0].strip()] = temp[1].strip()
    # res_dict['CSeq'] = res_lines[1].split(' ')[1]
    return res_dict

def rtp_response_parser(packet_bstr:bytes):
    packet_str = packet_bstr # bit manipulation so no need decoding
    header_size = 16
    header = packet_str[:header_size]
    payload = packet_str[header_size:]
    # header
    # (B1) Ver 2b, P 1b, X 1b, Cc 4b
    # (B2) M 1b, Payload Type 7b
    # (B3:B4) Seq Num 16b
    # (B5:B8) Time Stamp 32b
    # (B9:B12) SSRC 32b
    # (B13:B16) CSRC 32b
    res_dict = dict()
    # B3:B4
    res_dict['seq_num'] = header[2] << 8 | header[3]
    # B5:B8
    time_stamp = 0
    for i in range(4,8):
        time_stamp |= header[i] << 8 * (7 - i)
    res_dict['time_stamp'] = time_stamp
    # B9:B12
    # index of packet
    SSRC = 0
    for i in range(8,12):
        SSRC |= header[i] << 8 * (11 - i)
    res_dict['ind'] = SSRC
    # B13:B16
    # number of total packets
    CSRC = 0
    for i in range(12,16):
        CSRC |= header[i] << 8 * (15 - i)
    res_dict['total'] = CSRC

    res_dict['payload'] = payload
    # print(res_dict)
    return res_dict

def sdp_variable_parser(line):
    # format 1: a=AvgBitRate:integer;304018
    # format 2: a=length:npt=7.712000
    
    if ':' not in line:
        return
    line = line.split(':')
    if '=' not in line[0]:
        return
    line[0] = line[0].split('=')
    if ';' in line[1]: # format 1
        line[1] = line[1].split(';')
    elif '=' in line[1]: # format 2
        line[1] = line[1].split('=')
    else:
        return
    key = line[0][1]
    value = line[1][1]
    return (key, value)

# for testing
# lines = b'RTSP/1.0 200 OK\r\n\
#       CSeq: 2\r\n\
#       Content-Base: rtsp://example.com/media.mp4\r\n\
#       Content-Type: application/sdp\r\n\
#       Content-Length: 460\r\n\
# \r\n\
#       m=video 0 RTP/AVP 96\r\n\
#       a=control:streamid=0\r\n\
#       a=range:npt=0-7.741000\r\n\
#       a=length:npt=7.741000\r\n\
#       a=rtpmap:96 MP4V-ES/5544\r\n\
#       a=mimetype:string;"video/MP4V-ES"\r\n\
#       a=AvgBitRate:integer;304018\r\n\
#       a=StreamName:string;"hinted video track"\r\n\
#       m=audio 0 RTP/AVP 97\r\n\
#       a=control:streamid=1\r\n\
#       a=range:npt=0-7.712000\r\n\
#       a=length:npt=7.712000\r\n\
#       a=rtpmap:97 mpeg4-generic/32000/2\r\n\
#       a=mimetype:string;"audio/mpeg4-generic"\r\n\
#       a=AvgBitRate:integer;65790\r\n\
#       a=StreamName:string;"hinted audio track"'
# res = rtsp_response_parser(lines)
# print(res)