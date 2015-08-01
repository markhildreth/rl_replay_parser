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
        crc = self._read_unknown(replay_file, 20)
        header_start = self._read_unknown(replay_file, 24)

        data['header'] = self._read_properties(replay_file)
        unknown = self._read_unknown(replay_file, 8)
        data['level_info'] = self._read_level_info(replay_file)
        data['key_frames'] = self._read_key_frames(replay_file)
        data['network_frames'] = self._read_network_frames(replay_file)
        data['debug_logs'] = self._read_debug_logs(replay_file)
        data['goal_frame_info'] = self._read_goal_frame_infos(replay_file)
        data['packages'] = self._read_packages(replay_file)
        data['objects'] = self._read_objects(replay_file)
        data['names'] = self._read_names(replay_file)
        data['class_index'] = self._read_class_index(replay_file)
        data['class_net_cache'] = self._read_class_net_cache(replay_file)

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
        stream_byte_length = replay_file.read('uintle:32')
        # TODO: Figure this out at a later time
        replay_file.bytepos += stream_byte_length

    def _read_debug_logs(self, replay_file):
        log_size = replay_file.read('uintle:32')
        return [
            self._read_debug_log(replay_file)
            for x in range(log_size)
        ]

    def _read_debug_log(self, replay_file):
        frame = replay_file.read('uintle:32')
        name_length = replay_file.read('uintle:32')
        name = self._read_string(replay_file, name_length)
        msg_length = replay_file.read('uintle:32')
        msg = self._read_string(replay_file, msg_length)
        return {
            'frame': frame,
            'name' : name,
            'message' : msg
        }

    def _read_goal_frame_infos(self, replay_file):
        number_goal_frame_infos = replay_file.read('uintle:32')
        return [
            self._read_goal_frame_info(replay_file)
            for x in range(number_goal_frame_infos)
        ]

    def _read_goal_frame_info(self, replay_file):
        type_length = replay_file.read('uintle:32')
        type_name = self._read_string(replay_file, type_length)
        frame_number = replay_file.read('uintle:32')
        return {
            'type' : type_name,
            'frame_number': frame_number,
        }

    def _read_packages(self, replay_file):
        number_of_packages = replay_file.read('uintle:32')
        return [
            self._read_package(replay_file)
            for x in range(number_of_packages)
        ]

    def _read_package(self, replay_file):
        package_length = replay_file.read('uintle:32')
        return self._read_string(replay_file, package_length)

    def _read_objects(self, replay_file):
        number_of_objects = replay_file.read('uintle:32')
        return [
            self._read_object(replay_file)
            for x in range(number_of_objects)
        ]

    def _read_object(self, replay_file):
        object_length = replay_file.read('uintle:32')
        return self._read_string(replay_file, object_length)

    def _read_names(self, replay_file):
        number_of_names = replay_file.read('uintle:32')
        return [
            self._read_name(replay_file)
            for x in range(number_of_names)
        ]

    def _read_name(self, replay_file):
        name_length = replay_file.read('uintle:32')
        return self._read_string(replay_file, name_length)

    def _read_class_index(self, replay_file):
        number_of_classes = replay_file.read('uintle:32')
        return [
            self._read_class_index_item(replay_file)
            for x in range(number_of_classes)
        ]

    def _read_class_index_item(self, replay_file):
        class_name_size = replay_file.read('uintle:32')
        class_name = self._read_string(replay_file, class_name_size)
        class_id = replay_file.read('uintle:32')
        return {
            'class_name': class_name,
            'id' : class_id,
        }

    def _read_class_net_cache(self, replay_file):
        array_length = replay_file.read('uintle:32')
        return [
            self._read_class_net_cache_item(replay_file)
            for x in range(array_length)
        ]

    def _read_class_net_cache_item(self, replay_file):
        # Corresponds to the 'id' value in the class index.
        class_id = replay_file.read('uintle:32')
        # start/end represent range of the corresponding property elements in the
        # 'objects' array.
        class_index_start = replay_file.read('uintle:32')
        class_index_end = replay_file.read('uintle:32')
        length = replay_file.read('uintle:32')
        return {
            'class_id': class_id,
            'class_index_start' : class_index_start,
            'class_index_end' : class_index_end,
            'properties' : [
                self._read_class_net_cache_item_property_map(replay_file)
                for x in range(length)
            ]
        }

    def _read_class_net_cache_item_property_map(self, replay_file):
        property_index = replay_file.read('uintle:32')
        property_mapped_id = replay_file.read('uintle:32')
        return {
            'index': property_index,
            'id' : property_mapped_id,
        }


    def _pretty_byte_string(self, bytes_read):
        return ':'.join(format(ord(x), '#04x') for x in bytes_read)

    def _print_bytes(self, bytes_read):
        print('Hex read: {}'.format(self._pretty_byte_string(bytes_read)))

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

    def _sniff_bits(self, replay_file, size):
        print('****** Sniff Results *******')
        b = replay_file.read(size)
        print("Binary: {}".format(b.bin))
        if size % 4 == 0:
            print("Hex: {}".format(b.hex))
        if size >= 8:
            print("Int: {}".format(b.intle))
            print("Uint: {}".format(b.uintle))
        if size in [32, 64]:
            print("Float: {}".format(b.floatle))

if __name__ == '__main__':
    filename = sys.argv[1]
    if not filename.endswith('.replay'):
        sys.exit('Filename {} does not appear to be a valid replay file'.format(filename))

    with open(filename, 'rb') as replay_file:
        replay_bit_stream = bitstring.ConstBitStream(replay_file)
        results = ReplayParser(debug=False).parse(replay_bit_stream)
        try:
            pprint.pprint(results)
        except IOError as e:
            pass
