import pprint
import sys
import struct

class ReplayParser:
    def __init__(self, debug=False):
        self.debug = debug

    def parse(self, replay_file):
        unknown = replay_file.read(20)
        header_start = replay_file.read(24)

        results = self._read_properties(replay_file)
        pprint.pprint(results)

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
        name_length = self._read_number(replay_file, 4)
        property_name = self._read_string(replay_file, name_length)
        if self.debug: print("Property name: {}".format(property_name))

        if property_name == 'None':
            return None

        if self.debug: print("Reading type")
        type_length = self._read_number(replay_file, 4)
        type_name = self._read_string(replay_file, type_length)
        if self.debug: print("Type name: {}".format(type_name))

        if self.debug: print("Reading value")
        if type_name == 'IntProperty':
            value_length = self._read_number(replay_file, 8)
            value = self._read_number(replay_file, value_length)
        elif type_name == 'StrProperty':
            unknown = self._read_number(replay_file, 8)
            length = self._read_number(replay_file, 4)
            value = self._read_string(replay_file, length)
        elif type_name == 'FloatProperty':
            length = self._read_number(replay_file, 8)
            value = self._read_number(replay_file, length)
        elif type_name == 'NameProperty':
            unknown = self._read_number(replay_file, 8)
            length = self._read_number(replay_file, 4)
            value = self._read_string(replay_file, length)
        elif type_name == 'ArrayProperty':
            unknown = self._read_number(replay_file, 8)
            array_length = self._read_number(replay_file, 4)

            value = [
                self._read_properties(replay_file)
                for x in range(array_length)
            ]

        if self.debug: print("Value: {}".format(value))

        return { 'name' : property_name, 'value': value}

    def _print_bytes(self, bytes_read):
        if self.debug: print('Hex read: ' + ':'.join(hex(ord(x)) for x in bytes_read))

    def _read_number(self, replay_file, length):
        number_format = {
            1: '<B',
            2: '<H',
            4: '<I',
            8: '<Q',
        }[length]
        bytes_read = replay_file.read(length)
        self._print_bytes(bytes_read)
        value = struct.unpack(number_format, bytes_read)[0]
        if self.debug: print("Number read: {}".format(value))
        return value

    def _read_unknown(self, replay_file, num_bytes):
        bytes_read = replay_file.read(num_bytes)
        self._print_bytes(bytes_read)
        return bytes_read

    def _read_string(self, replay_file, length):
        bytes_read = replay_file.read(length)[0:-1]
        self._print_bytes(bytes_read)
        return bytes_read


if __name__ == '__main__':
    filename = sys.argv[1]
    if not filename.endswith('.replay'):
        sys.exit('Filename {} does not appear to be a valid replay file'.format(filename))

    with open(filename, 'rb') as replay_file:
        ReplayParser(debug=False).parse(replay_file)
