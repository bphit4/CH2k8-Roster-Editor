import struct


class Conference:
    def __init__(self, file_data, offset):
        self.file_data = file_data
        self.offset = offset

        self.conference_name_ptr = self.read_pointer(offset)
        self.conference_abbr_ptr = self.read_pointer(offset + 4)
        self.type = self.read_short(offset + 10)
        self.sort_order = self.read_short(offset + 12)
        self.founded = self.read_short(offset + 14)
        self.champs_order = self.read_short(offset + 16)
        self.final_fours = self.read_short(offset + 18)
        self.prev_yr_bids = self.read_short(offset + 20)
        self.rank = self.read_short(offset + 22)
        self.last_champ_order = self.read_short(offset + 24)
        self.presentation_id = self.read_short(offset + 26)
        self.tourney_slots = self.read_short(offset + 28)
        self.tourney_day = self.read_short(offset + 30)
        self.red = self.read_byte(offset + 32)
        self.green = self.read_byte(offset + 33)
        self.blue = self.read_byte(offset + 34)

    def read_pointer(self, offset):
        return struct.unpack(">I", self.file_data[offset:offset + 4])[0]

    def read_short(self, offset):
        return struct.unpack(">H", self.file_data[offset:offset + 2])[0]

    def read_byte(self, offset):
        return struct.unpack("B", self.file_data[offset:offset + 1])[0]

    def get_conference_name(self):
        return self.read_string(self.conference_name_ptr)

    def get_conference_abbr(self):
        return self.read_string(self.conference_abbr_ptr)

    def read_string(self, pointer):
        end = self.file_data.index(b'\x00', pointer)
        return self.file_data[pointer:end].decode('utf-8')
