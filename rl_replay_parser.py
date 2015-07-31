import pprint
import sys
import struct
import math

import bitstring

class ReplayParser:
    def __init__(self, debug=False):
        self.debug = debug

    def parse(self, replay_file):
        data = {}
        # TODO: CRC, version info, other stuff
        unknown = self._read_unknown(replay_file, 20)
        header_start = self._read_unknown(replay_file, 24)

        data['header'] = self._read_properties(replay_file)
        unknown = self._read_unknown(replay_file, 8)
        data['level_info'] = self._read_level_info(replay_file)
        data['key_frames'] = self._read_key_frames(replay_file)
        data['network_frames'] = self._read_network_frames(replay_file)
        return data

    def _read_properties(self, replay_file):
        results = {}

        while True:
            property_info = self._read_property(replay_file)
            if property_info:
                results[property_info['name']] = property_info['value']
            else:
                return results

    def _read_property(self, replay_file):
        if self.debug: print("Reading name")
        name_length = self._read_integer(replay_file, 4)
        property_name = self._read_string(replay_file, name_length)
        if self.debug: print("Property name: {}".format(property_name))

        if property_name == 'None':
            return None

        if self.debug: print("Reading type")
        type_length = self._read_integer(replay_file, 4)
        type_name = self._read_string(replay_file, type_length)
        if self.debug: print("Type name: {}".format(type_name))

        if self.debug: print("Reading value")
        if type_name == 'IntProperty':
            value_length = self._read_integer(replay_file, 8)
            value = self._read_integer(replay_file, value_length)
        elif type_name == 'StrProperty':
            unknown = self._read_integer(replay_file, 8)
            length = self._read_integer(replay_file, 4)
            value = self._read_string(replay_file, length)
        elif type_name == 'FloatProperty':
            length = self._read_integer(replay_file, 8)
            value = self._read_float(replay_file, length)
        elif type_name == 'NameProperty':
            unknown = self._read_integer(replay_file, 8)
            length = self._read_integer(replay_file, 4)
            value = self._read_string(replay_file, length)
        elif type_name == 'ArrayProperty':
            # I imagine that this is the length of bytes that the data
            # in the "array" actually take up in the file.
            unknown = self._read_integer(replay_file, 8)
            array_length = self._read_integer(replay_file, 4)

            value = [
                self._read_properties(replay_file)
                for x in range(array_length)
            ]

        if self.debug: print("Value: {}".format(value))

        return { 'name' : property_name, 'value': value}

    def _read_level_info(self, replay_file):
        map_names = []
        number_of_maps = self._read_integer(replay_file, 4)
        for x in range(number_of_maps):
            map_name_length = self._read_integer(replay_file, 4)
            map_name = self._read_string(replay_file, map_name_length)
            map_names.append(map_name)

        return map_names

    def _read_key_frames(self, replay_file):
        number_of_key_frames = self._read_integer(replay_file, 4)
        key_frames = [
            self._read_key_frame(replay_file)
            for x in range(number_of_key_frames)
        ]
        return key_frames

    def _read_key_frame(self, replay_file):
        time = self._read_float(replay_file, 4)
        frame = self._read_integer(replay_file, 4)
        file_position = self._read_integer(replay_file, 4)
        return {
            'time' : time,
            'frame' : frame,
            'file_position' : file_position
        }

    def _read_network_frames(self, replay_file):
        number_of_network_frames = self._read_integer(replay_file, 4)
        return [
            self._read_network_frame(replay_file)
        ]

        return [
            self._read_network_frame(replay_file)
            for x in range(number_of_network_frames)
        ]

    def _read_network_frame(self, replay_file):
        current_time = self._read_float(replay_file, 4)
        delta_time = self._read_float(replay_file, 4)

        return {
            'current_time' : current_time,
            'delta_time' : delta_time,
        }

    def _pretty_byte_string(self, bytes_read):
        return ':'.join(format(ord(x), '#04x') for x in bytes_read)

    def _print_bytes(self, bytes_read):
        print('Hex read: {}'.format(self._pretty_byte_string(bytes_read)))

    def _read_bits(self, replay_file, length, leftover = ''):
        source = leftover
        bytes_to_read = int(math.ceil((length - len(leftover)) / 8.0))
        source += ''.join('{0:08b}'.format(self._read_integer(replay_file, 1)) for x in range(bytes_to_read))

        data, new_leftover = source[0:length], source[length:]
        return int(data, 2), new_leftover

    def _read_integer(self, replay_file, length, signed=True):
        bits_read = replay_file.read(8 * length)
        if signed:
            return bits_read.intle
        else:
            return bits_read.uintle

    def _read_float(self, replay_file, length):
        return replay_file.read(8 * length).floatle

    def _read_unknown(self, replay_file, num_bytes):
        return replay_file.read(8 * num_bytes).hex

    def _read_string(self, replay_file, length):
        return replay_file.read(8 * length).bytes[:-1]

    def _sniff_bytes(self, replay_file, size):
        b = self._read_unknown(replay_file, size)
        print("**** BYTES ****")
        print("Bytes: {}".format(self._pretty_byte_string(b)))
        if size == 2:
            print("Short: Signed: {} Unsigned: {}".format(struct.unpack('<h', b), struct.unpack('<H', b)))
        else:
            print("Integer: Signed: {}, Unsigned: {}".format(struct.unpack('<i', b), struct.unpack('<I', b)))
            print("Float: {}".format(struct.unpack('<f', b)))


if __name__ == '__main__':
    filename = sys.argv[1]
    if not filename.endswith('.replay'):
        sys.exit('Filename {} does not appear to be a valid replay file'.format(filename))

    with open(filename, 'rb') as replay_file:
        replay_bit_stream = bitstring.ConstBitStream(replay_file)
        results = ReplayParser(debug=False).parse(replay_bit_stream)
        try:
            pprint.pprint(results)
            print('')
        except IOError as e:
            pass
