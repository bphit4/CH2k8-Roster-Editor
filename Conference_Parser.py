import struct

def read_big_endian_4_byte(data, offset):
    return int.from_bytes(data[offset:offset+4], byteorder='big', signed=False)

def read_string(data, offset):
    string = ''
    while True:
        char = struct.unpack('<H', data[offset:offset+2])[0]
        if char == 0:
            break
        string += chr(char)
        offset += 2
    return string

def parse_conference_info(data):
    conference_info_table_start = 0x34597C
    conference_info_table_end = 0x361198
    conference_block_length = 0xB94

    conferences = []
    for offset in range(conference_info_table_start, conference_info_table_end, conference_block_length):
        pointer = read_big_endian_4_byte(data, offset)
        conference_name_offset = offset + pointer
        conference_name = read_string(data, conference_name_offset)
        conferences.append((conference_name, offset))

    return conferences

with open("Roster2", "rb") as f:
    data = f.read()

conferences = parse_conference_info(data)

for conference in conferences:
    print(f"{conference[0]}: {hex(conference[1])}")
