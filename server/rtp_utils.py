def rtp_header_generator(sequence_number:int, timestamp:int ,SSRC, CSRC, payload_type=26):
  # default header info
  HEADER_SIZE = 12   # bytes
  VERSION = 0b10     # 2 bits -> current version 2
  PADDING = 0b0      # 1 bit
  EXTENSION = 0b0    # 1 bit
  CC = 0x0           # 4 bits
  MARKER = 0b0       # 1 bit
  # b0 -> v0 v1 p x c0 c1 c2 c3
  zeroth_byte = (VERSION << 6) | (PADDING << 5) | (EXTENSION << 4) | CC
  # b1 -> m pt0 pt1 pt2 pt3 pt4 pt5 pt6
  first_byte = (MARKER << 7) | payload_type
  # b2 -> s0 s1 s2 s3 s4 s5 s6 s7
  second_byte = sequence_number >> 8
  # b3 -> s8 s9 s10 s11 s12 s13 s14 s15
  third_byte = sequence_number & 0xFF
  # b4~b7 -> timestamp
  fourth_to_seventh_bytes = [
      (timestamp >> shift) & 0xFF for shift in (24, 16, 8, 0)
  ]
  shifts = (24, 16, 8, 0)
  # b8~b11 -> ssrc
  eigth_to_eleventh_bytes = []
  for i in range(len(shifts)):
      eigth_to_eleventh_bytes.append((SSRC%(256**(4-i))) >> shifts[i] & 0xFF)
  twelve_to_sixteen_bytes = []
  for i in range(len(shifts)):
      twelve_to_sixteen_bytes.append(((CSRC%(256**(4-i))) >> shifts[i]) & 0xFF)
  header = bytes((
      zeroth_byte,
      first_byte,
      second_byte,
      third_byte,
      *fourth_to_seventh_bytes,
      *eigth_to_eleventh_bytes,
      *twelve_to_sixteen_bytes,
  ))
#   print_header(header)
  return header


def print_header(header:bytes):
        # print header without SSRC
        for i, by in enumerate(header[:16]):
            s = ' '.join(f"{by:08b}")
            # break line after the third and seventh bytes
            print(s, end=' ' if i not in (3, 7, 11, 15) else '\n')