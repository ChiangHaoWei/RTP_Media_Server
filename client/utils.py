def rtsp_request_generator(req_dict, setup_type=None):
    version = "RTSP/1.0"
    if setup_type:
        req_dict['file_path'] += f"?streamid={setup_type}"
    req_str = f"{req_dict['command']} rtsp://{req_dict['file_path']} {version}"

    for key in req_dict:
        if key in {'command', 'file_path', 'port'}:
            continue
        req_str += f"{key}: {req_dict[key]}\r\n"
    # req_str += f"Transport: RTP/UDP;unicast;client_port={client_port}\r\n"
    return req_str.encode()

def rtsp_reponse_parser(res_bstr):
    res_lines = res_bstr.decode().split('\r\n')
    res_code = res_lines[0].split(' ')[1]
    res_dict = dict()
    res_dict['res_code'] = res_code
    for line in res_lines:
        temp = line.split(':')
        res_dict[temp[0].strip()] = temp[1].strip()
    # res_dict['CSeq'] = res_lines[1].split(' ')[1]
    return res_dict

def rtp_response_parser(packet_bstr:bytes):
    packet_str = packet_bstr.decode()
    header_size = 12
    header = packet_str[:header_size]
    payload = packet_str[header_size:]
    # header
    # (B1) Ver 2b, P 1b, X 1b, Cc 4b
    # (B2) M 1b, Payload Type 7b
    # (B3:B4) Seq Num 16b
    # (B5:B8) Time Stamp 32b
    # (B9:B12) SSI 32b
    # (ommitted) (B13:B16) CI 32b
    res_dict = dict()
    # B3:B4
    res_dict['seq_num'] = header[2] << 8 | header[3]
    # B5:B8
    time_stamp = 0
    for i in range(4,8):
        time_stamp |= header[i] << 8 * (7 - i)
    res_dict['time_stamp'] = time_stamp
    res_dict['payload'] = payload
    return res_dict